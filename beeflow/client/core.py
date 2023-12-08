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

import daemon
import typer

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import cli_connection
from beeflow.common import paths
from beeflow.wf_manager.resources import wf_utils


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

    @mgr.component('wf_manager', ('scheduler', 'celery'))
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

    @mgr.component('celery', ('redis',))
    def celery():
        """Start the celery task queue."""
        log = open_log('celery')
        # Setting --pool=solo to avoid preforking multiple processes
        return subprocess.Popen(['celery', '-A', 'beeflow.common.celery', 'worker', '--pool=solo'],
                                stdout=log, stderr=log)

    # Run this before daemonizing in order to avoid slow background start
    container_path = paths.redis_container()
    # If it exists, we assume that it actually has a valid container
    if not os.path.exists(container_path):
        print('Unpacking Redis image...')
        subprocess.check_call(['ch-convert', '-i', 'tar', '-o', 'dir',
                               bc.get('DEFAULT', 'redis_image'), container_path])

    @mgr.component('redis', ())
    def redis():
        """Start redis."""
        data_dir = 'data'
        os.makedirs(os.path.join(paths.redis_root(), data_dir), exist_ok=True)
        conf_name = 'redis.conf'
        container_path = paths.redis_container()
        # Dump the config
        conf_path = os.path.join(paths.redis_root(), conf_name)
        if not os.path.exists(conf_path):
            with open(conf_path, 'w', encoding='utf-8') as fp:
                # Don't listen on TCP
                print('port 0', file=fp)
                print('dir', os.path.join('/mnt', data_dir), file=fp)
                print('maxmemory 2mb', file=fp)
                print('unixsocket', os.path.join('/mnt', paths.redis_sock_fname()), file=fp)
                print('unixsocketperm 700', file=fp)
        cmd = [
            'ch-run',
            f'--bind={paths.redis_root()}:/mnt',
            container_path,
            'redis-server',
            '/mnt/redis.conf',
        ]
        log = open_log('redis')
        # Ran into a strange "Failed to configure LOCALE for invalid locale name."
        # from Redis, so setting LANG=C. This could have consequences for UTF-8
        # strings.
        env = dict(os.environ)
        env['LANG'] = 'C'
        return subprocess.Popen(cmd, env=env, stdout=log, stderr=log)

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


MIN_CHARLIECLOUD_VERSION = (0, 34)


def version_str(version):
    """Convert a version tuple to a string."""
    return '.'.join([str(part) for part in version])


def load_check_charliecloud():
    """Load the charliecloud module if it exists and check the version."""
    if not shutil.which('ch-run'):
        lmod = os.environ.get('MODULESHOME')
        sys.path.insert(0, lmod + '/init')
        from env_modules_python import module #noqa No need to import at top
        module("load", "charliecloud")
        # Try loading the Charliecloud module then test again
        if not shutil.which('ch-run'):
            warn('Charliecloud is not loaded. Please ensure that it is accessible'
                 ' on your path.\nIf it\'s not installed on your system, please refer'
                 ' to: \n https://hpc.github.io/charliecloud/install.html')
            sys.exit(1)
    cproc = subprocess.run(['ch-run', '-V'], capture_output=True, text=True,
                           check=True)
    version = cproc.stdout if cproc.stdout else cproc.stderr
    version = version.strip()
    if 'pre' in version:
        # Pre-release charliecloud in the format <version>~pre+<git_hash>
        print(f'Found Charliecloud {version}')
        version = version.split('~')[0]
        version = tuple(int(part) for part in version.split('.'))
    # Release versions are in the format 0.<version>
    else:
        version = tuple(int(part) for part in version.split('.'))
        print(f'Found Charliecloud {version_str(version)}')
    if version < MIN_CHARLIECLOUD_VERSION:
        warn('This version of Charliecloud is too old, please upgrade to at '
             f'least version {version_str(MIN_CHARLIECLOUD_VERSION)}')
        sys.exit(1)


def check_dependencies():
    """Check for various dependencies in the environment."""
    print('Checking dependencies...')
    # Check for Charliecloud and its version
    load_check_charliecloud()
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
    check_dependencies()
    mgr = init_components()
    beeflow_log = paths.log_fname('beeflow')
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
def reset(archive: bool = typer.Option(False, '--archive', '-a',
                                       help='Archive bee_workdir  before removal')):
    """Delete the bee_workdir directory."""
    # Check to see if the user is absolutely sure. Warning Message.
    absolutely_sure = ""
    while absolutely_sure != "y" or absolutely_sure != "n":
        # Get the user's bee_workdir directory
        directory_to_delete = os.path.expanduser(wf_utils.get_bee_workdir())
        print(f"A reset will remove this directory: {directory_to_delete}")

        absolutely_sure = input(
            """
Are you sure you want to reset?

Please ensure all workflows are complete before running a reset
Check the status of workflows by running 'beeflow list'

A reset will shutdown beeflow and its components.

A reset will delete the bee_workdir directory which results in:
Removing the archive of workflows executed.
Removing the archive of workflow containers.
Reset all databases associated with the beeflow app.
Removing all beeflow logs.

Beeflow configuration files from bee_cfg will remain.

Respond with yes(y)/no(n):  """)
        if absolutely_sure in ("n", "no"):
            # Exit out if the user didn't really mean to do a reset
            sys.exit()
        if absolutely_sure in ("y", "yes"):
            # Stop all of the beeflow processes
            resp = cli_connection.send(paths.beeflow_socket(), {'type': 'quit'})
            if resp is not None:
                print("Beeflow has been shutdown.")
                print("Waiting for components to cleanly stop.")
                # This wait is essential. It takes a minute to shut down.
                time.sleep(5)

            if os.path.exists(directory_to_delete):
                # Save the bee_workdir directory if the archive option was set
                if archive:
                    if os.path.exists(directory_to_delete + "/logs"):
                        shutil.copytree(directory_to_delete + "/logs",
                                        directory_to_delete + ".backup/logs")
                    if os.path.exists(directory_to_delete + "/container_archive"):
                        shutil.copytree(directory_to_delete + "/container_archive",
                                        directory_to_delete + ".backup/container_archive")
                    if os.path.exists(directory_to_delete + "/archives"):
                        shutil.copytree(directory_to_delete + "/archives",
                                        directory_to_delete + ".backup/archives")
                    if os.path.exists(directory_to_delete + "/workflows"):
                        shutil.copytree(directory_to_delete + "/workflows",
                                        directory_to_delete + ".backup/workflows")
                    print("Archive flag enabled,")
                    print("Existing logs, containers, and workflows backed up in:")
                    print(f"{directory_to_delete}.backup")
                shutil.rmtree(directory_to_delete)
                print(f"{directory_to_delete} has been removed.")
                sys.exit()
            else:
                print(f"{directory_to_delete} does not exist. Exiting.")
                sys.exit()
        print("Please respond with either the letter (y) or (n).")


@app.command()
def restart(foreground: bool = typer.Option(False, '--foreground', '-F',
            help='run in the foreground')):
    """Attempt to stop and restart the beeflow daemon."""
    stop()
    start(foreground)


def pull_to_tar(ref, tarball):
    """Pull a container from a registry and convert to tarball."""
    subprocess.check_call(['ch-image', 'pull', ref])
    subprocess.check_call(['ch-convert', '-i', 'ch-image', '-o', 'tar', ref, tarball])


@app.command()
def pull_deps(outdir: str = typer.Option('.', '--outdir', '-o',
                                         help='directory to store containers in')):
    """Pull required BEE containers and store in outdir."""
    load_check_charliecloud()
    neo4j_path = os.path.join(os.path.realpath(outdir), 'neo4j.tar.gz')
    pull_to_tar('neo4j:3.5.22', neo4j_path)
    redis_path = os.path.join(os.path.realpath(outdir), 'redis.tar.gz')
    pull_to_tar('redis', redis_path)
    print()
    print('The BEE dependency containers have been successfully downloaded. '
          'Please make sure to set the following options in your config:')
    print()
    print('[DEFAULT]')
    print('neo4j_image =', neo4j_path)
    print('redis_image =', redis_path)
