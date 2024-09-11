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
import datetime
import time
import importlib.metadata

import daemon
import typer

from beeflow.client import bee_client
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import cli_connection
from beeflow.common import paths
from beeflow.wf_manager.resources import wf_utils

from beeflow.common.deps import container_manager
from beeflow.common.deps import neo4j_manager
from beeflow.common.deps import redis_manager


class ComponentManager:
    """Component manager class."""

    def __init__(self):
        """Construct the component manager."""
        self.components = {}
        self.procs = {}

    def component(self, name, deps=None):
        """Return a decorator function to be called."""

        def wrap(fn):
            """Check to see if any components are disabled."""
            if bc.get('DEFAULT', 'remote_api') is False and 'remote_api' in name:
                return

            # Add the component to the list.
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
        return launch_with_gunicorn('beeflow.task_manager.task_manager:create_app()',
                                    paths.tm_socket(), stdout=fp, stderr=fp)

    @mgr.component('scheduler', ())
    def start_scheduler():
        """Start the scheduler."""
        fp = open_log('scheduler')
        # Using a function here because of the funny way that the scheduler's written
        return launch_with_gunicorn('beeflow.scheduler.scheduler:create_app()',
                                    paths.sched_socket(), stdout=fp, stderr=fp)

    @mgr.component('remote_api', ('wf_manager', 'task_manager'))
    def start_remote_api():
        """Start the remote API."""
        fp = open_log('remote_api')
        return launch_with_gunicorn('beeflow.remote.remote:create_app()',
                                    paths.remote_socket(), stdout=fp, stderr=fp)

    @mgr.component('celery', ('redis',))
    def celery():
        """Start the celery task queue."""
        log = open_log('celery')
        # Setting --pool=solo to avoid preforking multiple processes
        return subprocess.Popen(['celery', '-A', 'beeflow.common.deps.celery_manager',
                                 'worker', '--pool=solo'], stdout=log, stderr=log)

    # Run this before daemonizing in order to avoid slow background start
    # container_path = paths.redis_container()
    # If it exists, we assume that it actually has a valid container
    # if not os.path.exists(container_path):
        # print('Unpacking Redis image...')
        # subprocess.check_call(['ch-convert', '-i', 'tar', '-o', 'dir',
        #                       bc.get('DEFAULT', 'redis_image'), container_path])
    if not container_manager.check_container_dir('redis'):
        print('Unpacking Redis image...')
        container_manager.create_image('redis')

    if not container_manager.check_container_dir('neo4j'):
        print('Unpacking Neo4j image...')
        container_manager.create_image('neo4j')

    @mgr.component('neo4j-database', ('wf_manager',))
    def start_neo4j():
        """Start the neo4j graph database."""
        return neo4j_manager.start()

    @mgr.component('redis', ())
    def start_redis():
        """Start redis."""
        log = open_log('redis')
        return redis_manager.start(log)

    # Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
    if need_slurmrestd():
        @mgr.component('slurmrestd')
        def start_slurm_restd():
            """Start BEESlurmRestD. Returns a Popen process object."""
            bee_workdir = bc.get('DEFAULT', 'bee_workdir')
            slurmrestd_log = '/'.join([bee_workdir, 'logs', 'restd.log'])
            openapi_version = bc.get('slurm', 'openapi_version')
            slurm_args = f'-s openapi/{openapi_version}'
            # The following adds the db plugin we opted not to use for now
            # slurm_args = f'-s openapi/{openapi_version},openapi/db{openapi_version}'
            slurm_socket = paths.slurm_socket()
            subprocess.run(['rm', '-f', slurm_socket], check=True)
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

    version = importlib.metadata.version("hpc-beeflow")
    print(f'Starting beeflow {version}...')
    if not foreground:
        print('Run `beeflow core status` for more information.')
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
def info():
    """Get information about beeflow's installation."""
    version = importlib.metadata.version("hpc-beeflow")
    print(f"Beeflow version: {version}")
    print(f"bee_workflow directory: {paths.workdir()}")
    print(f"Log path: {paths.log_path()}")


@app.command()
def stop(query='yes'):
    """Stop the current running beeflow daemon."""
    # Check workflow states; warn if there are active states, pause running workflows
    workflow_list = bee_client.get_wf_list()
    concern_states = {'Running', 'Initializing', 'Waiting'}
    concern = {item for row in workflow_list for item in row}.intersection(concern_states)
    # For the interactive case
    if query == 'yes' and concern:
        ans = input("""
              **   There are running workflows.    **
              ** Running workflows will be paused. **

              Are you sure you want to kill beeflow components? [y/n] """)
    else:
        ans = 'y'
    if ans.lower() != 'y':
        return
    # Pause running or waiting workflows
    workflow_list = bee_client.get_wf_list()
    for _name, wf_id, state in workflow_list:
        if state in {'Running', 'Waiting'}:
            bee_client.pause(wf_id)
    resp = cli_connection.send(paths.beeflow_socket(), {'type': 'quit'})
    if resp is None:
        beeflow_log = paths.log_fname('beeflow')
        warn('Error: beeflow is not running on this system. It could be '
             'running on a different front end.\n'
             f'       Check the beeflow log: "{beeflow_log}".')
        sys.exit(1)
    # As long as it returned something, we should be good
    beeflow_log = paths.log_fname('beeflow')
    if query == "yes":
        print(f'Beeflow has stopped. Check the log at "{beeflow_log}".')


def archive_dir(dir_to_archive):
    """Archive directories for archive flag in reset."""
    archive_dirs = ['logs', 'container_archive', 'archives', 'workflows']
    date_str = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')}"
    backup_dir = f"{dir_to_archive}.{date_str}"
    for a_dir in archive_dirs:
        try:
            shutil.copytree(f"{dir_to_archive}/{a_dir}",
                            f"{backup_dir}/{a_dir}")
        except FileNotFoundError:
            pass
    print("Archive flag enabled.",
          "Existing logs, containers, and workflows backed up in:\n"
          f"{backup_dir}")


def handle_rm_error(err, dir_to_check, wf_list):
    """Handle IO error caused by either initializing workflows or nfs files."""
    # Check if only nfs mounts are causing the problem and ignore
    dir_list = os.listdir(dir_to_check)
    nfs_list = [x for x in dir_list if x.startswith('.nfs')]
    if dir_list and (dir_list != nfs_list):
        print(f"Unable to remove {dir_to_check} \n {err.strerror}")
        # Often initializing workflows cause a problem
        if any('Initializing' in sublist for sublist in wf_list):
            warn('Initializing workflows may have prevented removal.\n')
            print(f"Try removing {dir_to_check} manually, to complete reset.")


@app.command()
def reset(archive: bool = typer.Option(False, '--archive', '-a',
                                       help='Archive bee_workdir  before removal')):
    """Stop all components and delete the bee_workdir directory."""
    # Check workflow states; warn if there are active states.
    workflow_list = bee_client.get_wf_list()
    active_states = {'Running', 'Paused', 'Initializing', 'Waiting'}
    caution = ""
    if {item for row in workflow_list for item in row}.intersection(active_states):
        caution = """
        **************************************************************
          Caution: There are active workflows! They will be removed!
          Try 'beeflow list' to view them.
        **************************************************************
        """
    absolutely_sure = ""
    dir_to_delete = os.path.expanduser(wf_utils.get_bee_workdir())
    warn(f"\n    A reset will remove this directory: {dir_to_delete}\n")
    if archive:
        print("    Archive flag is set: logs, workflows and containers will be backed up.")
    print("""
    A reset will:
        Shutdown beeflow and all BEE components.
        Delete the bee_workdir directory which results in:
            Removing the archive of all workflows.
            Removing the archive of workflow containers
                (unless container_archive is configured elsewhere).
            Reset all databases associated with the beeflow app.
            Removing all beeflow logs.
    Beeflow configuration files from bee_cfg will not be deleted.
    """)
    warn(f"{caution}\nAre you sure you want to reset?")
    while absolutely_sure != "y" or absolutely_sure != "n":
        absolutely_sure = input("Respond with yes(y)/no(n): ")
        if absolutely_sure in ("n", "no"):
            # Exit out if the user didn't really mean to do a reset
            sys.exit()
        elif absolutely_sure in ("y", "yes"):
            # Stop all of the beeflow processes
            stop("quiet")
            print("Beeflow is shutting down.")
            print("Waiting for components to cleanly stop.")
            # This wait is essential. It takes a minute to shut down.
            time.sleep(5)

            # Save the bee_workdir directory if the archive option was set
            if archive:
                archive_dir(dir_to_delete)
            try:
                shutil.rmtree(dir_to_delete)
            except OSError as err:
                handle_rm_error(err, dir_to_delete, workflow_list)
            else:
                print(f"{dir_to_delete} has been removed.")
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
    pull_to_tar('neo4j:5.17', neo4j_path)
    redis_path = os.path.join(os.path.realpath(outdir), 'redis.tar.gz')
    pull_to_tar('redis', redis_path)
    print()
    print('The BEE dependency containers have been successfully downloaded. '
          'Please make sure to set the following options in your config:')
    print()
    print('[DEFAULT]')
    print('neo4j_image =', neo4j_path)
    print('redis_image =', redis_path)
