#!/usr/bin/env python3

"""beeflow.

This script manages the startup of the BEE daemons and supporting services.
If no arguments are given this script will start the BEEWorkflowManager,
BEETaskManager, and all required supporting services. If any combination of
services is specified using the appropriate flag(s) then ONLY those services
will be started.
"""
import os
import signal
import subprocess
import socket
import sys
import shutil
import time
import importlib.metadata

import daemon
import typer

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import cli_connection
from beeflow.common import paths


class ComponentManager:
    """Component manager class."""

    def __init__(self):
        """Construct the component manager."""
        self.components = {}
        self.procs = {}

    def component(self, name, deps=None):
        """Return a decorator function to be called."""

        def wrap(fn):
            """Add the component to the list."""
            self.components[name] = {
                'fn': fn,
                'deps': deps,
                'restart_count': 0,
                'failed': False,
            }

        return wrap

    def _validate(self, base_components):
        """Make sure that the components all exist and have valid deps."""
        missing = [name for name in base_components if name not in self.components]
        for component in self.components.values():
            if component['deps'] is None:
                continue
            for dep in component['deps']:
                if dep not in self.components:
                    missing.append(dep)
        if missing:
            raise RuntimeError(f'Missing/unknown component(s): {",".join(missing)}')

    def _find_order(self, base_components):
        """Find the order of the dependencies to launch."""
        s = base_components[:]
        levels = {name: 0 for name in self.components}
        while len(s) > 0:
            name = s.pop()
            if self.components[name]['deps'] is None:
                continue
            for dep in self.components[name]['deps']:
                levels[dep] = max(levels[name] + 1, levels[dep])
                # Detect a possible cycle
                if levels[dep] > len(self.components):
                    raise RuntimeError(f'There may be a cycle for the "{dep}" component')
                s.append(dep)
        levels = list(levels.items())
        levels.sort(key=lambda t: t[1], reverse=True)
        return [name for name, level in levels]

    def run(self, base_components):
        """Start and run everything."""
        # Determine if there are any missing components listed
        self._validate(base_components)
        # Determine the order to launch components in (note: this should just ignore cycles)
        order = self._find_order(base_components)
        print(f'Launching components in order: {order}')
        # Now launch the components
        for name in order:
            component = self.components[name]
            self.procs[name] = component['fn']()

    def poll(self):
        """Poll each process to check for errors, restart failed processes."""
        # Max number of times a component can be restarted
        max_restarts = bc.get('DEFAULT', 'max_restarts')
        for name in self.procs:  # noqa no need to iterate with items() since self.procs may be set
            component = self.components[name]
            if component['failed']:
                continue
            returncode = self.procs[name].poll()
            if returncode is not None:
                log = paths.log_fname(name)
                print(f'Component "{name}" failed, check log "{log}"')
                if component['restart_count'] >= max_restarts:
                    print(f'Component "{name}" has been restarted {max_restarts} '
                          'times, not restarting again')
                    component['failed'] = True
                else:
                    restart_count = component['restart_count']
                    print(f'Attempting restart {restart_count} of "{name}"...')
                    self.procs[name] = component['fn']()
                    component['restart_count'] += 1

    def status(self):
        """Return the statuses for each process in a dict."""
        return {
            name: 'RUNNING' if proc.poll() is None else 'FAILED'
            for name, proc in self.procs.items()
        }

    def kill(self):
        """Kill all components."""
        for name, proc in self.procs.items():
            print(f'Killing {name}')
            proc.terminate()


def warn(*pargs):
    """Print a red warning message."""
    typer.secho(' '.join(pargs), fg=typer.colors.RED, file=sys.stderr)


def launch_with_gunicorn(module, sock_path, *args, **kwargs):
    """Launch a component with Gunicorn."""
    # Setting the timeout to infinite, since sometimes the gdb can take too long
    return subprocess.Popen(['gunicorn', module, '--timeout', '0', '-b', f'unix:{sock_path}'],
                            *args, **kwargs)


def open_log(component):
    """Determine the log for the component, open and return it."""
    log = paths.log_fname(component)
    return open(log, 'a', encoding='utf-8')


def need_slurmrestd():
    """Check if slurmrestd is needed."""
    return (bc.get('DEFAULT', 'workload_scheduler') == 'Slurm'
            and not bc.get('slurm', 'use_commands'))


def init_components():
    """Initialize the components and component manager."""
    mgr = ComponentManager()

    # Slurmrestd will be started only if we're running with Slurm and
    # slurm::use_commands is not True

    @mgr.component('wf_manager', ('scheduler',))
    def start_wfm():
        """Start the WFM."""
        fp = open_log('wf_manager')
        return launch_with_gunicorn('beeflow.wf_manager.wf_manager:create_app()',
                                    paths.wfm_socket(), stdout=fp, stderr=fp)

    tm_deps = []
    if need_slurmrestd():
        tm_deps.append('slurmrestd')

    @mgr.component('task_manager', tm_deps)
    def start_task_manager():
        """Start the TM."""
        fp = open_log('task_manager')
        return launch_with_gunicorn('beeflow.task_manager:flask_app', paths.tm_socket(),
                                    stdout=fp, stderr=fp)

    @mgr.component('scheduler', ())
    def start_scheduler():
        """Start the scheduler."""
        fp = open_log('scheduler')
        # Using a function here because of the funny way that the scheduler's written
        return launch_with_gunicorn('beeflow.scheduler.scheduler:create_app()',
                                    paths.sched_socket(), stdout=fp, stderr=fp)

    # Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
    if need_slurmrestd():
        @mgr.component('slurmrestd')
        def start_slurm_restd():
            """Start BEESlurmRestD. Returns a Popen process object."""
            bee_workdir = bc.get('DEFAULT', 'bee_workdir')
            slurmrestd_log = '/'.join([bee_workdir, 'logs', 'restd.log'])
            openapi_version = bc.get('slurm', 'openapi_version')
            slurm_args = f'-s openapi/{openapi_version}'
            slurm_socket = paths.slurm_socket()
            subprocess.run(['rm', '-f', slurm_socket], check=True)
            # log.info("Attempting to open socket: {}".format(slurm_socket))
            fp = open(slurmrestd_log, 'w', encoding='utf-8') # noqa
            cmd = ['slurmrestd']
            cmd.extend(slurm_args.split())
            cmd.append(f'unix:{slurm_socket}')
            return subprocess.Popen(cmd, stdout=fp, stderr=fp)

    return mgr


MIN_CHARLIECLOUD_VERSION = (0, 32)


def version_str(version):
    """Convert a version tuple to a string."""
    return '.'.join([str(part) for part in version])


def check_dependencies():
    """Check for various dependencies in the environment."""
    print('Checking dependencies...')
    # Check for Charliecloud and it's version
    if not shutil.which('ch-run'):
        warn('Charliecloud is not loaded. Please ensure that it is accessible on your path.')
        sys.exit(1)
    cproc = subprocess.run(['ch-run', '-V'], capture_output=True, text=True,
                           check=True)
    version = cproc.stdout if cproc.stdout else cproc.stderr
    version = version.strip()
    version = tuple(int(part) for part in version.split('.'))
    print(f'Found Charliecloud {version_str(version)}')
    if version < MIN_CHARLIECLOUD_VERSION:
        warn('This version of Charliecloud is too old, please upgrade to at '
             f'least version {version_str(MIN_CHARLIECLOUD_VERSION)}')
        sys.exit(1)
    # Check for the flux API
    if bc.get('DEFAULT', 'workload_scheduler') == 'Flux':
        try:
            import flux  # noqa needed to check whether flux api is actually installed
        except ModuleNotFoundError:
            warn('Failed to import flux Python API. Please make sure you can '
                 'use flux in your environment.')
            sys.exit(1)


class Beeflow:
    """Beeflow class for handling the main loop."""

    def __init__(self, mgr, base_components):
        """Create the Beeflow class."""
        self.mgr = mgr
        self.base_components = base_components
        self.quit = False

    def loop(self):
        """Run the main loop."""
        print(f'Running on {socket.gethostname()}')
        self.mgr.run(self.base_components)
        with cli_connection.server(paths.beeflow_socket()) as server:
            while not self.quit:
                # Handle a message from the client, if there is one
                self.handle_client(server)
                # Poll the components
                self.mgr.poll()
                time.sleep(1)
        # Kill everything, if possible
        self.mgr.kill()

    def handle_client(self, server):
        """Handle a message from the client."""
        try:
            client = server.accept()
            if client is None:
                return
            msg = client.get()
            resp = None
            if msg['type'] == 'status':
                resp = {
                    'components': self.mgr.status(),
                }
                print('Returned status info.')
            elif msg['type'] == 'quit':
                self.quit = True
                resp = 'shutting down'
                print('Shutting down.')
            client.put(resp)
        except cli_connection.BeeflowConnectionError as err:
            print(f'connection failed: {err}')


def daemonize(mgr, base_components):
    """Start beeflow as a daemon, monitoring all processes."""
    def handle_terminate(signum, stack): # noqa
        """Handle a terminate signal."""
        # Kill all subprocesses
        mgr.kill()
        sys.exit(1)

    # Now set signal handling, the log and finally daemonize
    signal_map = {
        signal.SIGINT: handle_terminate,
        signal.SIGTERM: handle_terminate,
    }
    fp = open_log('beeflow')
    with daemon.DaemonContext(signal_map=signal_map, stdout=fp, stderr=fp, stdin=fp,
                              umask=0o002):
        Beeflow(mgr, base_components).loop()


app = typer.Typer(no_args_is_help=True)


@app.command()
def start(foreground: bool = typer.Option(False, '--foreground', '-F',
          help='run in the foreground')):
    """Start all BEE components."""
    mgr = init_components()
    beeflow_log = paths.log_fname('beeflow')
    check_dependencies()
    sock_path = paths.beeflow_socket()
    if bc.get('DEFAULT', 'workload_scheduler') == 'Slurm' and not need_slurmrestd():
        warn('Not using slurmrestd. Command-line interface will be used.')
    # Note: there is a possible race condition here, however unlikely
    if os.path.exists(sock_path):
        # Try to contact for a status
        try:
            resp = cli_connection.send(sock_path, {'type': 'status'})
        except (ConnectionResetError, ConnectionRefusedError):
            resp = None
        if resp is None:
            # Must be dead, so remove the socket path
            try:
                os.remove(sock_path)
            except FileNotFoundError:
                pass
        else:
            # It's already running, so print an error and exit
            warn(f'Beeflow appears to be running. Check the beeflow log: "{beeflow_log}"')
            sys.exit(1)
    print('Starting beeflow...')
    if not foreground:
        print(f'Check "{beeflow_log}" or run `beeflow core status` for more information.')
    # Create the log path if it doesn't exist yet
    path = paths.log_path()
    os.makedirs(path, exist_ok=True)
    base_components = ['wf_manager', 'task_manager', 'scheduler']
    if foreground:
        try:
            Beeflow(mgr, base_components).loop()
        except KeyboardInterrupt:
            mgr.kill()
    else:
        daemonize(mgr, base_components)


@app.command()
def status():
    """Check the status of beeflow and the components."""
    resp = cli_connection.send(paths.beeflow_socket(), {'type': 'status'})
    if resp is None:
        beeflow_log = paths.log_fname('beeflow')
        warn('Cannot connect to the beeflow daemon, is it running? Check the '
             f'log at "{beeflow_log}".')
        sys.exit(1)
    print('beeflow components:')
    for comp, stat in resp['components'].items():
        print(f'{comp} ... {stat}')


@app.command()
def stop():
    """Stop the current running beeflow daemon."""
    stop_msg = ("\n** Please ensure all workflows are complete before stopping beeflow. **"
                + "\n** Check the status of workflows by running 'beeflow list'.    **"
                + "\nAre you sure you want to kill beeflow components? [y/n] ")
    ans = input(stop_msg)
    if ans.lower() != 'y':
        return
    resp = cli_connection.send(paths.beeflow_socket(), {'type': 'quit'})
    if resp is None:
        beeflow_log = paths.log_fname('beeflow')
        warn('Error: beeflow is not running on this system. It could be '
             'running on a different front end.\n'
             f'       Check the beeflow log: "{beeflow_log}".')
        sys.exit(1)
    # As long as it returned something, we should be good
    beeflow_log = paths.log_fname('beeflow')
    print(f'Beeflow has stopped. Check the log at "{beeflow_log}".')


@app.command()
def restart(foreground: bool = typer.Option(False, '--foreground', '-F',
            help='run in the foreground')):
    """Attempt to stop and restart the beeflow daemon."""
    stop()
    start(foreground)


@app.callback(invoke_without_command=True)
def version_callback(version: bool = False):
    """Beeflow."""
    # Print out the current version of the app, and then exit
    # Note above docstring gets used in the help menu
    if version:
        version = importlib.metadata.version("hpc-beeflow")
        print(version)
