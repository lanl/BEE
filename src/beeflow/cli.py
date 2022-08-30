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
import shutil
import getpass
import time
import string
import tempfile
from subprocess import PIPE
from configparser import NoOptionError
import beeflow.common.log as bee_logging
from beeflow.common.config_driver import BeeConfig

log = bee_logging.setup_logging(level='DEBUG')
restd_log = bee_logging.setup_logging(level='DEBUG')
nginx_log = bee_logging.setup_logging(level='DEBUG')
redis_log = bee_logging.setup_logging(level='DEBUG')


def get_script_path():
    """Construct a path to beeflow script install tree."""
    return os.path.dirname(os.path.realpath(__file__))


# Workflow manager and task manager need to be opened with PIPE for their stdout/stderr
def start_slurm_restd(bc, args):
    """Start BEESlurmRestD. Returns a Popen process object."""
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=restd_log,
                             logfile='restd.log')
    slurmrestd_log = '/'.join([bee_workdir, 'logs', 'restd.log'])
    # Load gdb config from config file if exists
    try:
        bc.userconfig['slurmrestd']
    except KeyError:
        restd_dict = {
            'slurm_socket': '/tmp/slurm_{}_{}.sock'.format(os.getlogin(), 100 + bc.offset),
        }
        # Add section (writes to config file)
        bc.modify_section('user', 'slurmrestd', restd_dict)
    if args.config_only:
        return None
    slurm_socket = bc.userconfig.get('slurmrestd', 'slurm_socket')
    subprocess.Popen(['rm', '-f', slurm_socket])
    log.info("Attempting to open socket: {}".format(slurm_socket))
    return subprocess.Popen([f"slurmrestd unix:{slurm_socket} > {slurmrestd_log} 2>&1"],
                            stdout=PIPE, stderr=PIPE, shell=True)


def start_workflow_manager(bc, args):
    """Start BEEWorkflowManager. Returns a Popen process object."""
    # Load gdb config from config file if exists
    try:
        bc.userconfig['workflow_manager']
    except KeyError:
        wfm_dict = {
            'listen_port': bc.default_wfm_port,
        }
        # Add section (writes to config file)
        bc.modify_section('user', 'workflow_manager', wfm_dict)
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    use_wsgi = bc.userconfig.get('DEFAULT', 'use_wsgi')
    if use_wsgi == "True":
        proc = subprocess.Popen(['gunicorn', '--ini', 
            get_script_path() + '/data/gunicorn_configs/wf_manager.ini'])
            #get_script_path() + '/data/gunicorn_configs/wf_manager.ini'],
            #                stdout=PIPE, stderr=PIPE)
    else:
        proc = subprocess.Popen(["python", get_script_path() + "/wf_manager.py",
                            userconfig_file], stdout=PIPE, stderr=PIPE)
    return proc


def start_task_manager(bc, args):
    """Start BEETaskManager. Returns a Popen process object."""
    # Load gdb config from config file if exists
    try:
        bc.userconfig['task_manager']
    except KeyError:
        tm_dict = {
            'listen_port': bc.default_tm_port,
            'container_runtime': 'Charliecloud'
        }
        # Add section (writes to config file)
        bc.modify_section('user', 'task_manager', tm_dict)
    finally:
        if args.job_template:
            tm_dict = {'job_template': args.job_template}
            bc.modify_section('user', 'task_manager', tm_dict)
    if args.config_only:
        return None

    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
    use_wsgi = bc.userconfig.get('DEFAULT', 'use_wsgi')
    if use_wsgi == "True":
        proc = subprocess.Popen(['gunicorn', '--ini', 
            get_script_path() + '/data/gunicorn_configs/task_manager.ini'])
            #get_script_path() + '/data/gunicorn_configs/task_manager.ini'],
            #                stdout=PIPE, stderr=PIPE)
    else:
        proc = subprocess.Popen(["python", get_script_path() + "/task_manager.py",
                            userconfig_file], stdout=PIPE, stderr=PIPE)
    return proc


def start_nginx(bc, args):
    """Start the nginx server. Returns a Popen process object."""
    #nginx_handler = bee_logging.save_log(bc, nginx_log, logfile='nginx_launch.log')
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=nginx_log,
                             logfile='nginx_start.log')
    # Think about logfile name. Logging charliecloud not nginx itself
    try:
        bc.userconfig['nginx']
    except KeyError:
        nginx_dict = {
            'nginx_image': '/usr/projects/beedev/nginx_new.tgz',
            'nginx_image_mntdir': '/tmp',
        }
        # Add section (writes to config file)
        bc.modify_section('user','graphdb',graphdb_dict)
    
    if args.config_only:
        return None

    if shutil.which("ch-tar2dir") == None or shutil.which("ch-run") == None:
        nginx_log.error("ch-tar2dir or ch-run not found. Charliecloud required for nginx container.")
        return None

    # Setup subprocess output
    stdout = sys.stdout
    stderr = sys.stderr

    wfm_port = bc.userconfig['workflow_manager']['listen_port']
    tm_port = bc.userconfig['task_manager']['listen_port']
    sched_port  = bc.userconfig['scheduler']['listen_port']
    options = { 'wfm_listen_port': wfm_port, 'tm_listen_port': tm_port,
                'sched_listen_port': sched_port, 'user': getpass.getuser()}
    tm_port = bc.userconfig['task_manager']['listen_port']
    nginx_img     = bc.userconfig.get('nginx','nginx_image')
    nginx_img_mntdir = bc.userconfig.get('nginx','nginx_image_mntdir')

    # Create nginx configuration directory if it doesn't exist
    nginx_config_dir = bee_workdir + '/nginx_config'
    os.makedirs(nginx_config_dir, exist_ok=True)
    os.makedirs(nginx_config_dir + '/log', exist_ok=True)
    os.makedirs(nginx_config_dir + '/run', exist_ok=True)
    os.makedirs(nginx_config_dir + '/config', exist_ok=True)

    # Create Nginx config based on config template
    with open(get_script_path() + '/data/nginx_config_template/bee.conf.in', 'r') as f_in:
        input_config = string.Template(f_in.read())
        output_config = input_config.substitute(options)
        with open(nginx_config_dir + '/config/bee.conf', 'w') as f_out:
            f_out.write(output_config)

    # Container directory if we don't already have one
    container_dir = nginx_img_mntdir + "/nginx_" + getpass.getuser()
    container_path = container_dir + '/nginx_new'
    if not os.path.isdir(container_dir):
        os.makedirs(container_dir, exist_ok=True)
        try:
            print('Creating image')
            cp = subprocess.run(["ch-tar2dir", str(nginx_img), 
                str(container_dir)], stdout=stdout, stderr=stderr, check=True)
        except subprocess.CalledProcessError as cp:
            nginx_log.error("ch-tar2dir failed")
            shutil.rmtree(container_dir)
            if args.debug:
                nginx_log.error("Nginx container mount directory " + container_dir + " removed")
            return None

        
    if args.debug:
        nginx_log.info("Nginx container mount directory " + container_dir + " created")

    try:
        # Kill all previous nginx processes 
        subprocess.run(['pkill', '-u', os.getlogin(), 'nginx'])
        # Kill all previous gunicorn instances
        subprocess.run(['pkill', '-u', os.getlogin(), 'gunicorn'])
        proc = subprocess.Popen([
            "ch-run",
            "-b", 
            # Put logs in main bee_workdir log directory /logs
            # Add nginx_logs directory to main logs directory
            nginx_config_dir + "/log:/var/log/nginx",
            "-b", 
            nginx_config_dir + "/run:/run",
            "-b", 
            nginx_config_dir + "/config:/etc/nginx/conf.d",
            container_path,
            "--",
            "service",
            "nginx",
            "start"
        ], stdout=stdout, stderr=stderr)
    except FileNotFoundError as e:
        gdb_log.error("nginx failed to start.")
        return None


def start_scheduler(bc, args):
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
        bc.modify_section('user', 'scheduler', sched_dict)

    if args.config_only:
        return None
    # Either use the userconfig file argument specified to beeflow,
    # or assume the default path to ~/.config/beeflow/bee.conf.
    if args.userconfig_file:
        userconfig_file = args.userconfig_file
    else:
        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')

    use_wsgi = bc.userconfig.get('DEFAULT', 'use_wsgi')
    if use_wsgi == "True":
        proc = subprocess.Popen(['gunicorn', '--ini', 
            get_script_path() + '/data/gunicorn_configs/scheduler.ini'],
                            stdout=PIPE, stderr=PIPE)
    else:
        proc = subprocess.Popen(["python", get_script_path() + "/scheduler/scheduler.py",
                            userconfig_file], stdout=PIPE, stderr=PIPE)

    return proc


def start_build(args):
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
                          stdout=PIPE, stderr=PIPE)


def start_redis(bc, args):
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    redis_img = bc.userconfig.get('redis','redis_image')
    redis_img_mntdir = bc.userconfig.get('redis','redis_image_mntdir')
    redis_port = bc.userconfig['redis']['listen_port']
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=nginx_log,
                             logfile='redis.log')

    # Setup subprocess output
    stdout = sys.stdout
    stderr = sys.stderr


    container_dir = redis_img_mntdir + "/redis_" + getpass.getuser()
    container_path = container_dir + '/redis'
    data_dir = container_dir + '/data'
    if not os.path.isdir(container_dir):
        os.makedirs(container_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        try:
            cp = subprocess.run(["ch-tar2dir", str(redis_img), 
                str(container_dir)], check=True)
            shutil.copyfile(get_script_path() + '/data/redis_config/redis.conf', data_dir + '/redis.conf')
        except subprocess.CalledProcessError as cp:
            redis_log.error("ch-tar2dir failed")
            shutil.rmtree(container_dir)
            if args.debug:
                redis_log.error("Nginx container mount directory " + container_dir + " removed")
            return None

    try:
        proc = subprocess.Popen([
            "ch-run",
            container_path,
            "-b", 
            data_dir + ":/etc/redis/",
            "--",
            "redis-server",
            "/etc/redis/redis.conf",
            "--port", 
            redis_port
        ], stdout=subprocess.DEVNULL, stderr=stderr)
    except FileNotFoundError as e:
        gdb_log.error("nginx failed to start.")
        return None


    
def create_pid_file(proc, pid_file, bc):
    """Create a new PID file."""
    os.makedirs(bc.userconfig.get('DEFAULT', 'bee_workdir'), exist_ok=True)
    with open('{}/{}'.format(str(bc.userconfig.get('DEFAULT', 'bee_workdir')),
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
    parser.add_argument("--nginx", action="store_true", help="start NginX")
    parser.add_argument("--redis", action="store_true", help="start Redis")
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
    start_all = not any([args.wfm, args.nginx, args.redis, args.tm, args.restd, args.sched]) or all([args.wfm, args.nginx, args.redis, args.tm, args.restd, args.sched])
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
    bc = BeeConfig(**config_params)
    # If workdir argument exists, over-write
    if args.bee_workdir:
        bc.modify_section('user', 'DEFAULT', {'bee_workdir': bc.resolve_path(args.bee_workdir)})
    # If workload_scheduler argument exists, over-write
    if args.workload_scheduler:
        bc.modify_section('user', 'task_manager', {'workload_scheduler': args.workload_scheduler})
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    # Setup logging based on args.debug
    _ = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='beeflow.log')
    if log is None:
        # Something went wrong
        return 1


    use_wsgi = bc.userconfig.get('DEFAULT', 'use_wsgi')
    if args.build:
        proc = start_build(args)
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
    try:
        workload_scheduler = bc.userconfig.get('DEFAULT', 'workload_scheduler')
    except NoOptionError:
        workload_scheduler = 'Slurm'
        bc.modify_section('user', 'DEFAULT', {'workload_scheduler': workload_scheduler})
    if args.nginx or start_all:
        proc = start_nginx(bc, args)
        #if not args.config_only:
            #if proc is None:
            #    log.error('NGINX failed to start. Exiting.')
            #    return 1
            #create_pid_file(proc, 'nginx.pid', bc)
            #wait_list.append(('NGINX', proc))
            #log.info('Loading NGINX')
    if args.redis or start_all:
        proc = start_redis(bc, args)

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
        proc = start_scheduler(bc, args)
        if not args.config_only and not use_wsgi:
            if proc is None:
                log.error('Scheduler failed to start. Exiting.')
                print('Scheduler failed to start. Exiting.', file=sys.stderr)
                return 1
            create_pid_file(proc, 'sched.pid', bc)
            wait_list.append(('Scheduler', proc))
            log.info('Loading Scheduler')
    if args.wfm or start_all:
        proc = start_workflow_manager(bc, args)
        if not args.config_only and not use_wsgi:
            if proc is None:
                log.error('Workflow Manager failed to start. Exiting.')
                return 1
            create_pid_file(proc, 'wfm.pid', bc)
            wait_list.append(('Workflow Manager', proc))
            log.info('Loading Workflow Manager')
    if args.tm or start_all:
        proc = start_task_manager(bc, args)
        if not args.config_only and not use_wsgi:
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
