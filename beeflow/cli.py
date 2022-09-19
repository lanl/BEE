#!/usr/bin/env python3

"""beeflow.

This script manages the startup of the BEE daemons and supporting services.
If no arguments are given this script will start the BEEWorkflowManager,
BEETaskManager, and all required supporting services. If any combination of
services is specified using the appropriate flag(s) then ONLY those services
will be started.
"""
from contextlib import contextmanager
import os
import signal
import subprocess
import sys
import time

import daemon
import typer

from beeflow.common.config_driver import BeeConfig as bc


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

    def kill(self):
        """Kill all components."""
        for name, proc in self.procs.items():
            print(f'Killing {name}')
            proc.terminate()


mgr = ComponentManager()


def launch_with_gunicorn(module, socket, *args, **kwargs):
    """Launch a component with Gunicorn."""
    # Setting the timeout to infinite, since sometimes the gdb can take too long
    return subprocess.Popen(['gunicorn', module, '--timeout', '0', '-b', f'unix:{socket}'],
                            *args, **kwargs)


def log_path():
    """Return the main log path."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    return os.path.join(bee_workdir, 'logs')


def log_fname(name):
    """Determine the log file name."""
    return os.path.join(log_path(), f'{name}.log')


def open_log(name):
    """Determine the log for the component, open and return it."""
    log = log_fname(name)
    return open(log, 'a', encoding='utf-8')


@mgr.component('wf_manager', ('scheduler', 'db'))
def start_wfm():
    """Start the WFM."""
    fp = open_log('wf_manager')
    socket = bc.get('workflow_manager', 'socket')
    return launch_with_gunicorn('beeflow.wf_manager.wf_manager:create_app()',
                                socket, stdout=fp, stderr=fp)


@mgr.component('task_manager', ('slurmrestd', 'db'))
def start_task_manager():
    """Start the TM."""
    fp = open_log('task_manager')
    socket = bc.get('task_manager', 'socket')
    return launch_with_gunicorn('beeflow.task_manager:flask_app', socket, stdout=fp, stderr=fp)


@mgr.component('scheduler', ('db',))
def start_scheduler():
    """Start the scheduler."""
    fp = open_log('scheduler')
    socket = bc.get('scheduler', 'socket')
    # Using a function here because of the funny way that the scheduler's written
    return launch_with_gunicorn('beeflow.scheduler.scheduler:create_app()', socket, stdout=fp,
                                stderr=fp)


# Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
@mgr.component('slurmrestd')
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


@mgr.component('db')
def start_db():
    """Start the main database (Redis or something else)."""
    # TODO
    return subprocess.Popen(['sleep', '10'])


# TODO: Not sure if this start_build() function is needed here
# @mgr.component('builder')
# def start_build():
#    """Start builder.
#
#    Start build tool with task described as Dict.
#    :rtype: instance of Popen
#    """
#    print('args.build:', args.build)
#    userconfig_file = args.build[0]
#    build_args = args.build[1]
#    print(["python", "-m", "beeflow.common.build_interfaces",
#          userconfig_file, build_args],)
#    return subprocess.run(["python", "-m", "beeflow.common.build_interfaces",
#                          userconfig_file, build_args], check=False,
#                          stdout=cli_log, stderr=cli_log)


def handle_terminate(signum, stack): # noqa
    """Handle a terminate signal."""
    # Kill all subprocesses
    mgr.kill()
    sys.exit(1)


def beeflow_loop(base_components):
    """Run the main loop."""
    mgr.run(base_components)
    while True:
        mgr.poll()
        time.sleep(5)


def daemonize(base_components):
    """Start beeflow as a daemon, monitoring all processes."""

    @contextmanager
    def pidfile_manager(fname):
        """Manage the PID file.

        Note: this doesn't lock anything like in PEP 3143. It just creates the pidfile,
        then deletes it.
        """
        pid = os.getpid()
        with open(fname, 'w', encoding='utf-8') as fp:
            fp.write(str(pid))
        try:
            yield
        finally:
            os.remove(fname)

    # Get the pidfile and check if it exists already
    pidfile = bc.get('DEFAULT', 'beeflow_pidfile')
    # Note: there is a possible race condition here, however unlikely
    if os.path.exists(pidfile):
        with open(pidfile, encoding='utf-8') as fp:
            pid = fp.read()
            raise RuntimeError(f'beeflow seems to already be running (PID {pid})')
    # Now set signal handling, the log and finally daemonize
    signal_map = {
        signal.SIGINT: handle_terminate,
        signal.SIGTERM: handle_terminate,
    }
    fp = open_log('beeflow')
    with daemon.DaemonContext(signal_map=signal_map, stdout=fp, stderr=fp, stdin=fp,
                              umask=0o002, pidfile=pidfile_manager(pidfile)):
        beeflow_loop(base_components)


app = typer.Typer()


@app.command()
def start(foreground: bool = typer.Option(False, '--foreground', '-F',
          help='run in the foreground')):
    """Attempt to daemonize if not in debug and start all BEE components."""
    # Create the log path if it doesn't exist yet
    path = log_path()
    os.makedirs(path, exist_ok=True)
    base_components = ['wf_manager', 'task_manager', 'scheduler']
    if foreground:
        try:
            beeflow_loop(base_components)
        except KeyboardInterrupt:
            mgr.kill()
    else:
        daemonize(base_components)


@app.command()
def stop():
    """Stop the current running beeflow daemon."""
    pidfile = bc.get('DEFAULT', 'beeflow_pidfile')
    if not os.path.exists(pidfile):
        sys.exit("Error: beeflow doesn't appear to be running")
    with open(pidfile, encoding='utf-8') as fp:
        pid = int(fp.read())
        print(f'Killing pid {pid}')
        try:
            os.kill(pid, signal.SIGTERM)
        except (OverflowError, PermissionError):
            sys.exit("Error: beeflow is not running on this system. It could be "
                     "running on a different front end.")
        beeflow_log = log_fname('beeflow')
        print(f'Check the beeflow log: "{beeflow_log}"')


def main():
    """Start the beeflow app."""
    bc.init()
    app()


if __name__ == '__main__':
    main()
