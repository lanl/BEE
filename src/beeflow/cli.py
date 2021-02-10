#!/usr/bin/env python3

"""BEEStart.

This script manages the startup of the BEE daemons and supporting services.
If no arguments are given this script will start the BEEWorkflowManager,
BEETaskManager, and all required supporting services. If any combination of
services is specified using the appropriate flag(s) then ONLY those services
will be started.
"""

import argparse
import getpass
import os
import shutil
import subprocess
import sys
import tempfile
import time
import platform
from subprocess import PIPE
from configparser import NoOptionError
import beeflow.common.log as bee_logging
from beeflow.common.config_driver import BeeConfig

log = bee_logging.setup_logging(level='DEBUG')
restd_log = bee_logging.setup_logging(level='DEBUG') 
gdb_log = bee_logging.setup_logging(level='DEBUG')

def StartGDB(bc, args):
    """Start the graph database. Returns a Popen process object."""
    gdb_handler = bee_logging.save_log(bc, gdb_log, logfile='gdb_launch.log')
    # Load gdb config from config file if exists
    try:
        bc.userconfig['graphdb']
    except KeyError:
        graphdb_dict = {
            'hostname': 'localhost',
            'dbpass': 'password',
            'bolt_port': bc.default_bolt_port,
            'http_port': bc.default_http_port,
            'https_port': bc.default_https_port ,
            'gdb_image': '/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz',
            'gdb_image_mntdir': '/tmp',
        }
        # Add section (writes to config file)
        bc.modify_section('user','graphdb',graphdb_dict)
    if args.config_only:
       return None
    if shutil.which("ch-tar2dir") == None or shutil.which("ch-run") == None:
        gdb_log.error("ch-tar2dir or ch-run not found. Charliecloud required for neo4j container.")
        return None

    # Setup subprocess output
    stdout = sys.stdout
    stderr = sys.stderr


    # Read the config file back in
    db_hostname = bc.userconfig.get('graphdb','hostname')
    db_password = bc.userconfig.get('graphdb','dbpass')
    bolt_port   = bc.userconfig.get('graphdb','bolt_port')
    http_port   = bc.userconfig.get('graphdb','http_port')
    https_port  = bc.userconfig.get('graphdb','https_port')
    gdb_img     = bc.userconfig.get('graphdb','gdb_image')
    gdb_img_mntdir = bc.userconfig.get('graphdb','gdb_image_mntdir')

    container_dir = tempfile.mkdtemp(suffix="_" + getpass.getuser(), prefix="gdb_", dir=str(gdb_img_mntdir))
    if args.debug:
        gdb_log.info("GraphDB container mount directory " + container_dir + " created")

    try:
        cp = subprocess.run(["ch-tar2dir",str(gdb_img),str(container_dir)], stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError as cp:
        gdb_log.error("ch-tar2dir failed")
        shutil.rmtree(container_dir)
        if args.debug:
            gdb_log.error("GraphDB container mount directory " + container_dir + " removed")
        return None

    newdir = os.path.split(container_dir)[1]

    container_path = container_dir + "/" + os.listdir(str(container_dir))[0]
    # Make the certificates directory
    container_certs_path = os.path.join(container_path, 'var/lib/neo4j/certificates')
    os.makedirs(container_certs_path, exist_ok=True)
    if args.debug:
        gdb_log.info('Created certificates directory %s', container_certs_path)
    # Setup working path data
    gdb_workdir = os.path.join(bc.userconfig.get('DEFAULT','bee_workdir'),
                               newdir)
    gdb_config_path = os.path.join(gdb_workdir, "conf")
    os.makedirs(gdb_config_path, exist_ok=True)
    gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf", gdb_config_path + "/neo4j.conf")
    if args.debug:
        gdb_log.info(gdb_configfile)

    cfile = open(gdb_configfile, "rt")
    data = cfile.read()
    cfile.close()
    data = data.replace("#dbms.connector.bolt.listen_address=:7687", "dbms.connector.bolt.listen_address=:" + str(bolt_port))
    data = data.replace("#dbms.connector.http.listen_address=:7474", "dbms.connector.http.listen_address=:" + str(http_port))
    data = data.replace("#dbms.connector.https.listen_address=:7473", "dbms.connector.https.listen_address=:" + str(https_port))
    cfile = open(gdb_configfile, "wt")
    cfile.write(data)
    cfile.close()

    gdb_data_path = os.path.join(gdb_workdir, "data")
    os.makedirs(gdb_data_path, exist_ok=True)

    gdb_log_path = os.path.join(gdb_workdir, "logs")
    os.makedirs(gdb_log_path, exist_ok=True)

    gdb_run_path = os.path.join(gdb_workdir, "run")
    os.makedirs(gdb_run_path, exist_ok=True)

    gdb_certs_path = os.path.join(gdb_workdir, "certificates")
    os.makedirs(gdb_certs_path, exist_ok=True)

    try:
        cp = subprocess.run([
            "ch-run","--set-env=" + container_path + "/ch/environment","-b",
            gdb_config_path + ":/var/lib/neo4j/conf","-b",
            gdb_data_path + ":/data",
            "-b",
            gdb_log_path + ":/logs",
            "-b",
            gdb_run_path + ":/var/lib/neo4j/run",
            container_path,
            "--",
            "neo4j-admin",
            "set-initial-password",
            str(db_password)
        ], stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError as cp:
        gdb_log.error("neo4j-admin set-initial-password failed")
        print("neo4j-admin set-initial-password failed", file=sys.stderr)
        return None

    try:
        proc = subprocess.Popen([
            "ch-run",
            "--set-env=" + container_path + "/ch/environment",
            "-b",
            gdb_config_path + ":/var/lib/neo4j/conf",
            "-b",
            gdb_data_path + ":/data",
            "-b",
            gdb_log_path + ":/logs",
            "-b",
            gdb_run_path + ":/var/lib/neo4j/run",
            "-b",
            gdb_certs_path + ":/var/lib/neo4j/certificates",
            container_path,
            "--",
            "neo4j",
            "start",
        ], stdout=stdout, stderr=stderr)
    except FileNotFoundError as e:
        gdb_log.error("neo4j failed to start.")
        return None

    return proc

# Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
def StartSlurmRestD(bc, args):
    """Start BEESlurmRestD. Returns a Popen process object."""

    restd_handler = bee_logging.save_log(bc, restd_log, logfile='restd.log')
    slurmrestd_log = '/'.join([bc.userconfig.get('DEFAULT','bee_workdir'),'logs','restd.log']) 
    # Load gdb config from config file if exists
    try:
        bc.userconfig['slurmrestd']
    except KeyError:
        restd_dict = {
            'slurm_socket': '/tmp/slurm_{}_{}.sock'.format(os.getlogin(), 100 + bc.offset),
        }
        # Add section (writes to config file)
        bc.modify_section('user','slurmrestd',restd_dict)
    if args.config_only:
        return None
    slurm_socket = bc.userconfig.get('slurmrestd','slurm_socket')
    subprocess.Popen(['rm','-f',slurm_socket])
    log.info("Attempting to open socket: {}".format(slurm_socket))
    return subprocess.Popen([f"slurmrestd unix:{slurm_socket} > {slurmrestd_log} 2>&1"],
                            stdout=PIPE, stderr=PIPE, shell=True)

def StartWorkflowManager(bc, args):
    """Start BEEWorkflowManager. Returns a Popen process object."""

    # Load gdb config from config file if exists
    try:
        bc.userconfig['workflow_manager']
    except KeyError:
        wfm_dict = {
            'listen_port': bc.default_wfm_port,
        }
        # Add section (writes to config file)
        bc.modify_section('user','workflow_manager',wfm_dict)
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to BEEStart,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", "-m", "beeflow.wf_manager",
                            userconfig_file],
                            stdout=PIPE, stderr=PIPE)

def StartTaskManager(bc, args):
    """Start BEETaskManager. Returns a Popen process object."""
    # Load gdb config from config file if exists
    try:
        bc.userconfig['task_manager']
    except KeyError:
        if args.job_template:
            job_template = args.job_template
        tm_dict = {
            'listen_port': bc.default_tm_port,
            'container_runtime': 'Charliecloud'
        }
        # Add section (writes to config file)
        bc.modify_section('user','task_manager',tm_dict)
    finally:
        if args.job_template:
            tm_dict= {'job_template': args.job_template}
            bc.modify_section('user','task_manager',tm_dict)
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to BEEStart,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", "-m", "beeflow.task_manager",
                            userconfig_file],
                            stdout=PIPE, stderr=PIPE)

def StartScheduler(bc, args):
    """Start BEEScheduler.

    Start BEEScheduler and return the process object.
    :rtype: instance of Popen
    """
    # Load scheduler config if exists
    try:
        bc.userconfig['scheduler']
    except KeyError:
        sched_dict = {
            'listen_port': bc.default_sched_port
        }
        # Add section (writes to config file)
        bc.modify_section('user','scheduler',sched_dict)
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to BEEStart,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", "-m", "beeflow.scheduler.scheduler",
                            '--config-file',userconfig_file],
                            stdout=PIPE, stderr=PIPE)

def StartCloudLauncher(bc, args):
    """Start the BEE Cloud Launcher.

    Start the BEE Cloud Launcher and return the process object.
    :rtype: instance of Popen
    """
    try:
        bc.userconfig['cloud']
    except KeyError:
        cloud_dict = {
            'node_count': 1,
            'provider': 'Google',
        }
        bc.modify_section('user', 'cloud', cloud_dict)

    if args.config_only:
        return None
    # Either use the userconfig file argument specified to BEEStart,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    return subprocess.Popen(["python", "-m", "beeflow.cloud_launcher", userconfig_file], stdout=PIPE, stderr=PIPE)

def create_pid_file(proc, pid_file, bc):
    """Create a new PID file."""
    os.makedirs(bc.userconfig.get('DEFAULT','bee_workdir'), exist_ok=True)
    with open('{}/{}'.format(str(bc.userconfig.get('DEFAULT','bee_workdir')),pid_file), 'w') as fp:
        fp.write(str(proc.pid))

def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-d", "--debug", action="store_true",
                        help="enable debugging output\nIf debug is specified all output will go to the console.\nOnly one BEE service may be launched by BEEStart if debug is requested.")
    parser.add_argument("--wfm", action="store_true", help="start the BEEWorkflowManager (implies --gdb)")
    parser.add_argument("--gdb", action="store_true", help="start the configured graph database")
    parser.add_argument("--tm", action="store_true", help="start the BEETaskManager")
    parser.add_argument("--restd", action="store_true", help="start the Slurm REST daemon")
    parser.add_argument("--sched", action="store_true", help="start the BEEScheduler")
    parser.add_argument("--cloud", action="store_true", help="start the Cloud Launcher")
    parser.add_argument("--userconfig-file", help="specify the path to a user configuration file")
    parser.add_argument("--bee-workdir", help="specify the path for BEE to store temporary files and artifacts")
    parser.add_argument("--job-template", help="specify path of job template.")
    parser.add_argument("--workload-scheduler", help="specify workload scheduler")
    parser.add_argument("--config-only", action="store_true", help="create a valid configuration file, but don't launch bee services.")
    parser.add_argument("--sleep-time", default=4, type=int,
                        help="amount of time to sleep before checking processes")
    return parser.parse_args(args)

def main():
    args = parse_args()
    start_all = not any([args.wfm, args.tm, args.gdb, args.restd, args.sched, args.cloud]) or all([args.wfm, args.tm, args.gdb, args.restd, args.sched, args.cloud])
    if args.debug and not (sum([args.wfm, args.tm, args.gdb, args.restd, args.sched, args.cloud]) == 1):
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
    bc = BeeConfig(**config_params)
    # If workdir argument exists, over-write
    if args.bee_workdir:
        bc.modify_section('user', 'DEFAULT', {'bee_workdir':bc.resolve_path(args.bee_workdir)} )
    # If workload_scheduler argument exists, over-write
    if args.workload_scheduler:
        bc.modify_section('user', 'task_manager', {'workload_scheduler':args.workload_scheduler} )
    # Setup logging based on args.debug
    handler = bee_logging.save_log(bc, log, logfile='beeflow.log')
    if log is None:
        # Something went wrong
        return 1

    # Start all processes
    wait_list = [] # List of processes to wait for
    # Only start slurmrestd if workload_scheduler is Slurm (default)
    try:
        workload_scheduler = bc.userconfig.get('DEFAULT','workload_scheduler')
    except NoOptionError:
        workload_scheduler = 'Slurm'
        bc.modify_section('user', 'DEFAULT', {'workload_scheduler':workload_scheduler} )
    if workload_scheduler == 'Slurm':
        if args.restd or start_all:
            proc = StartSlurmRestD(bc, args)
            if not args.config_only:
                if proc is None:
                    log.error('slurmrestd failed to start. Exiting.')
                    return 1
                # Don't append the graph database to list of processes to wait for
                log.info('Starting slurmrestd based on userconfig file.')
    if args.sched or start_all:
        proc = StartScheduler(bc, args)
        if not args.config_only:
            if proc is None:
                log.error('Scheduler failed to start. Exiting.')
                print('Scheduler failed to start. Exiting.', file=sys.stderr)
                return 1
            create_pid_file(proc, 'sched.pid', bc)
            wait_list.append(('Scheduler', proc))
            log.info('Loading Scheduler')
    if args.gdb or start_all:
        proc = StartGDB(bc, args)
        if not args.config_only:
            if proc is None:
                log.error('Graph Database failed to start. Exiting.')
                return 1
            # Don't append the graph database to list of processes to wait for
            log.info('Loading Graph Database')
    if args.wfm or start_all:
        proc = StartWorkflowManager(bc, args)
        if not args.config_only:
            if proc is None:
                log.error('Workflow Manager failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'wfm.pid', bc)
            wait_list.append(('Workflow Manager', proc))
            log.info('Loading Workflow Manager')
    if args.tm or start_all:
        proc = StartTaskManager(bc, args)
        if not args.config_only:
            if proc is None:
                log.error('Task Manager failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'tm.pid', bc)
            wait_list.append(('Task Manager', proc))
            log.info('Loading Task Manager')
    if args.cloud or start_all:
        proc = StartCloudLauncher(bc, args)
        if not args.config_only:
            if proc is None:
                log.error('Cloud Launcher failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'cloud.pid', bc)
            wait_list.append(('Cloud Launcher', proc))
            log.info('Loading Cloud Launcher')
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
