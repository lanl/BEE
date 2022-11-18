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
        """Poll each process to check for errors."""
        for name, proc in self.procs.items():
            returncode = proc.poll()
            if returncode is not None:
                log = log_fname(name)
                print(f'Component "{name}" failed, check log "{log}"')

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


MGR = ComponentManager()


def warn(*pargs):
    """Print a red warning message."""
    typer.secho(' '.join(pargs), fg=typer.colors.RED, file=sys.stderr)


def launch_with_gunicorn(module, sock_path, *args, **kwargs):
    """Launch a component with Gunicorn."""
    # Setting the timeout to infinite, since sometimes the gdb can take too long
    return subprocess.Popen(['gunicorn', module, '--timeout', '0', '-b', f'unix:{sock_path}'],
                            *args, **kwargs)


def log_path():
    """Return the main log path."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    return os.path.join(bee_workdir, 'logs')


def log_fname(component):
    """Determine the log file name for the given component."""
    return os.path.join(log_path(), f'{component}.log')


def open_log(component):
    """Determine the log for the component, open and return it."""
    log = log_fname(component)
    return open(log, 'a', encoding='utf-8')


@MGR.component('wf_manager', ('scheduler',))
def start_wfm():
    """Start the WFM."""
    fp = open_log('wf_manager')
    sock_path = bc.get('workflow_manager', 'socket')
    return launch_with_gunicorn('beeflow.wf_manager.wf_manager:create_app()',
                                sock_path, stdout=fp, stderr=fp)


@MGR.component('task_manager', ('slurmrestd',))
def start_task_manager():
    """Start the TM."""
    fp = open_log('task_manager')
    sock_path = bc.get('task_manager', 'socket')
    return launch_with_gunicorn('beeflow.task_manager:flask_app', sock_path, stdout=fp, stderr=fp)


@MGR.component('scheduler', ())
def start_scheduler():
    """Start the scheduler."""
    fp = open_log('scheduler')
    sock_path = bc.get('scheduler', 'socket')
    # Using a function here because of the funny way that the scheduler's written
    return launch_with_gunicorn('beeflow.scheduler.scheduler:create_app()', sock_path, stdout=fp,
                                stderr=fp)


# Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
@MGR.component('slurmrestd')
def start_slurm_restd():
    """Start BEESlurmRestD. Returns a Popen process object."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    slurmrestd_log = '/'.join([bee_workdir, 'logs', 'restd.log'])
    slurm_socket = bc.get('slurmrestd', 'slurm_socket')
    slurm_args = bc.get('slurmrestd', 'slurm_args')
    slurm_args = slurm_args if slurm_args is not None else ''
    subprocess.run(['rm', '-f', slurm_socket], check=True)
    # log.info("Attempting to open socket: {}".format(slurm_socket))
    fp = open(slurmrestd_log, 'w', encoding='utf-8') # noqa
    cmd = ['slurmrestd']
    cmd.extend(slurm_args.split())
    cmd.append(f'unix:{slurm_socket}')
    return subprocess.Popen(cmd, stdout=fp, stderr=fp)


def handle_terminate(signum, stack): # noqa
    """Handle a terminate signal."""
    # Kill all subprocesses
    MGR.kill()
    sys.exit(1)


MIN_CHARLIECLOUD_VERSION = (0, 27)


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
        sock_path = bc.get('DEFAULT', 'beeflow_socket')
        with cli_connection.server(sock_path) as server:
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


def daemonize(base_components):
    """Start beeflow as a daemon, monitoring all processes."""
    # Now set signal handling, the log and finally daemonize
    signal_map = {
        signal.SIGINT: handle_terminate,
        signal.SIGTERM: handle_terminate,
    }
    fp = open_log('beeflow')
    with daemon.DaemonContext(signal_map=signal_map, stdout=fp, stderr=fp, stdin=fp,
                              umask=0o002):
        Beeflow(MGR, base_components).loop()


app = typer.Typer(no_args_is_help=True)


@app.command()
def start(foreground: bool = typer.Option(False, '--foreground', '-F',
          help='run in the foreground')):
    """Attempt to daemonize if not in debug and start all BEE components."""
    beeflow_log = log_fname('beeflow')
    check_dependencies()
    sock_path = bc.get('DEFAULT', 'beeflow_socket')
    # Note: there is a possible race condition here, however unlikely
    if os.path.exists(sock_path):
        # Try to contact for a status
        resp = cli_connection.send(sock_path, {'type': 'status'})
        if resp is None:
            # Must be dead, so remove the socket path
            os.remove(sock_path)
        else:
            # It's already running, so print an error and exit
            warn(f'Beeflow appears to be running. Check the beeflow log: "{beeflow_log}"')
            sys.exit(1)
    print('Starting beeflow...')
    if not foreground:
        print(f'Check "{beeflow_log}" or run `beeflow status` for more information.')
    # Create the log path if it doesn't exist yet
    path = log_path()
    os.makedirs(path, exist_ok=True)
    base_components = ['wf_manager', 'task_manager', 'scheduler']
    if foreground:
        try:
            Beeflow(MGR, base_components).loop()
        except KeyboardInterrupt:
            MGR.kill()
    else:
        daemonize(base_components)


@app.command()
def status():
    """Check the status of beeflow and the components."""
    sock_path = bc.get('DEFAULT', 'beeflow_socket')
    resp = cli_connection.send(sock_path, {'type': 'status'})
    if resp is None:
        beeflow_log = log_fname('beeflow')
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
                + "\n** Check the status of workflows by running 'beeclient listall'.    **"
                + "\nAre you sure you want to kill beeflow components? [y/n] ")
    ans = input(stop_msg)
    if ans.lower() != 'y':
        return
    sock_path = bc.get('DEFAULT', 'beeflow_socket')
    resp = cli_connection.send(sock_path, {'type': 'quit'})
    if resp is None:
        beeflow_log = log_fname('beeflow')
        warn('Error: beeflow is not running on this system. It could be '
             'running on a different front end.\n'
             f'       Check the beeflow log: "{beeflow_log}".')
        sys.exit(1)
    # As long as it returned something, we should be good
    beeflow_log = log_fname('beeflow')
    print(f'Beeflow has stopped. Check the log at "{beeflow_log}".')


@app.callback(invoke_without_command=True)
def version_callback(version: bool = False):
    """Beeflow."""
    # Print out the current version of the app, and then exit
    # Note above docstring gets used in the help menu
    if version:
        version = importlib.metadata.version("hpc-beeflow")
        print(version)


def main():
    """Start the beeflow app."""
    bc.init()
    app()


if __name__ == '__main__':
    main()
