#!/usr/bin/env python3

"""beeflow.

This script manages the startup of the BEE daemons and supporting services.
If no arguments are given this script will start the BEEWorkflowManager,
BEETaskManager, and all required supporting services. If any combination of
services is specified using the appropriate flag(s) then ONLY those services
will be started.
"""

import argparse
import os
import subprocess
import sys
import time
import getpass
from subprocess import PIPE
from configparser import NoOptionError
import beeflow.common.log as bee_logging
from beeflow.common.config_driver import BeeConfig as bc

log = bee_logging.setup_logging(level='DEBUG')
restd_log = bee_logging.setup_logging(level='DEBUG')


def get_script_path():
    """Construct a path to beeflow script install tree."""
    return os.path.dirname(os.path.realpath(__file__))


# Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
def start_slurm_restd(bc, args):
    """Start BEESlurmRestD. Returns a Popen process object."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=restd_log,
                             logfile='restd.log')
    slurmrestd_log = '/'.join([bee_workdir, 'logs', 'restd.log'])
    if args.config_only:
        return None
    slurm_socket = bc.get('slurmrestd', 'slurm_socket')
    slurm_args = bc.get('slurmrestd', 'slurm_args')
    slurm_args = slurm_args if slurm_args is not None else ''
    subprocess.Popen(['rm', '-f', slurm_socket])
    log.info("Attempting to open socket: {}".format(slurm_socket))
    return subprocess.Popen([f"slurmrestd {slurm_args} unix:{slurm_socket} > {slurmrestd_log} 2>&1"],
                            stdout=PIPE, stderr=PIPE, shell=True)


def start_workflow_manager(bc, args, cli_log):
    """Start BEEWorkflowManager. Returns a Popen process object."""
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", get_script_path() + "/wf_manager.py",
                            userconfig_file], stdout=cli_log, stderr=cli_log)


def start_task_manager(bc, args, cli_log):
    """Start BEETaskManager. Returns a Popen process object."""
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", get_script_path() + "/task_manager.py",
                            userconfig_file], stdout=cli_log, stderr=cli_log)


def start_scheduler(bc, args, cli_log):
    """Start BEEScheduler.

    Start BEEScheduler and return the process object.
    :rtype: instance of Popen
    """
    if args.config_only:
        return None
    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", get_script_path() + "/scheduler/scheduler.py",
                            '--config-file', userconfig_file],
                            stdout=cli_log, stderr=cli_log)


def start_build(args, cli_log):
    """Start builder.

    Start build tool with task described as Dict.
    :rtype: instance of Popen
    """
    print('args.build:', args.build)
    userconfig_file = args.build[0]
    build_args = args.build[1]
    print(["python", "-m", "beeflow.common.build_interfaces",
          userconfig_file, build_args],)
    return subprocess.run(["python", "-m", "beeflow.common.build_interfaces",
                          userconfig_file, build_args], check=False,
                          stdout=cli_log, stderr=cli_log)


def create_pid_file(proc, pid_file, bc):
    """Create a new PID file."""
    os.makedirs(bc.get('DEFAULT', 'bee_workdir'), exist_ok=True)
    with open('{}/{}'.format(str(bc.get('DEFAULT', 'bee_workdir')),
                             pid_file), 'w') as fp:
        fp.write(str(proc.pid))


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-d", "--debug", action="store_true",
                        help="enable debugging output\nIf debug is specified all output will go to the console.\nOnly one BEE service may be launched by beeflow if debug is requested.")
    parser.add_argument("--wfm", action="store_true", help="start the BEEWorkflowManager (implies --gdb)")
    parser.add_argument("--tm", action="store_true", help="start the BEETaskManager")
    parser.add_argument("--restd", action="store_true", help="start the Slurm REST daemon")
    parser.add_argument("--sched", action="store_true", help="start the BEEScheduler")
    parser.add_argument("--userconfig-file", help="specify the path to a user configuration file")
    parser.add_argument("--bee-workdir", help="specify the path for BEE to store temporary files and artifacts")
    parser.add_argument("--job-template", help="specify path of job template.")
    parser.add_argument("--workload-scheduler", help="specify workload scheduler")
    parser.add_argument("--build", metavar=("CONF_FILE", "TASK_ARGS"), nargs=2,
                        help="build a container based on a task specification")
    parser.add_argument("--config-only", action="store_true", help="create a valid configuration file, but don't launch bee services.")
    parser.add_argument("--sleep-time", default=4, type=int,
                        help="amount of time to sleep before checking processes")
    return parser.parse_args(args)


def main():
    """Execute beeflow components in logical sequence."""
    args = parse_args()
    start_all = not any([args.wfm, args.tm, args.restd, args.sched]) or all([args.wfm, args.tm, args.restd, args.sched])
    if args.debug and not sum([args.wfm, args.tm,  args.restd, args.sched]) == 1:
        print("DEBUG requested, exactly one service must be specified",
              file=sys.stderr)
        return 1
    # Pass configuration file params to config_driver.py
    config_params = {}
    if args.userconfig_file:
        config_params['userconfig'] = args.userconfig_file
    if args.bee_workdir:
        config_params['bee_workdir'] = args.bee_workdir
    if args.workload_scheduler:
        config_params['workload_scheduler'] = args.workload_scheduler
    if args.job_template:
        config_params['job_template'] = args.job_template
    bc.init(**config_params)
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    # Setup logging based on args.debug
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='beeflow.log')
    if log is None:
        # Something went wrong
        return 1

    # Set up a CLI log to log output from the subprocesses
    if args.debug:
        cli_log = sys.stdout
    else:
        cli_log_fname = os.path.join(os.path.join(bee_workdir, 'logs'), 'cli.log')
        cli_log = open(cli_log_fname, 'w')
    if args.build:
        proc = start_build(args, cli_log)
        if proc is None:
            log.error('Builder failed to initialize. Exiting.')
            return 1
        create_pid_file(proc, 'builder.pid', bc)
        log.info('Loading Builder...')
        return 0
    if args.config_only:
        return 0
    # Start all processes
    wait_list = []  # List of processes to wait for
    # Only start slurmrestd if workload_scheduler is Slurm (default)
    workload_scheduler = bc.get('DEFAULT', 'workload_scheduler')
    if workload_scheduler == 'Slurm':
        if args.restd or start_all:
            proc = start_slurm_restd(bc, args)
            if not args.config_only:
                if proc is None:
                    log.error('slurmrestd failed to start. Exiting.')
                    return 1
                # Don't append the graph database to list of processes to wait for
                log.info('Starting slurmrestd based on userconfig file.')
    if args.sched or start_all:
        proc = start_scheduler(bc, args, cli_log)
        if not args.config_only:
            if proc is None:
                log.error('Scheduler failed to start. Exiting.')
                print('Scheduler failed to start. Exiting.', file=sys.stderr)
                return 1
            create_pid_file(proc, 'sched.pid', bc)
            wait_list.append(('Scheduler', proc))
            log.info('Loading Scheduler')
    if args.wfm or start_all:
        proc = start_workflow_manager(bc, args, cli_log)
        if not args.config_only:
            if proc is None:
                log.error('Workflow Manager failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'wfm.pid', bc)
            wait_list.append(('Workflow Manager', proc))
            log.info('Loading Workflow Manager')
    if args.tm or start_all:
        proc = start_task_manager(bc, args, cli_log)
        if not args.config_only:
            if proc is None:
                log.error('Task Manager failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'tm.pid', bc)
            wait_list.append(('Task Manager', proc))
            log.info('Loading Task Manager')
    if args.config_only:
        return 0

    time.sleep(args.sleep_time)
    # Check if any processes have finished early
    for name, proc in wait_list:
        exit_code = proc.poll()
        if exit_code is not None:
            log.error(f'{name} failed to start. Exiting.')

    # Wait for everything to finish, if debug, otherwise just exit now
    if args.debug:
        while len(wait_list) > 0:
            name, proc = wait_list.pop()
            exit_code = proc.wait()
            if exit_code != 0:
                log.error('Error running %s', name)

    return 0


if __name__ == "__main__":
    sys.exit(main())
# Ignoring C0103: bc is a common object in  beeflow. ignoring the snake case naming convention break
# Ignoring W1202: fstring logging isn't causing us problems at the moment, and improves readability
# Ignoring R1732: Should be using "with" context with Popen...but really we need to s/Popen/run/.
#                 deferring this warning until we use the appropriate subprocess method.
# Ignoring W0102: Dangerous default for args. Fix is beyond the scope of my PR. Deferring for now.
# Ignoring E501,C0301: Long help string text is more readable than breaking stirngs up, perhaps.
# Ignoring R091[1,5]: "Too many statements" is realted to code complexity. Distributed systems are
#                     complex. Perhaps we should just accept the complexity.
# pylama:ignore=C0103,W1202,R1732,W0102,E501,C0301,R0911,R0915
