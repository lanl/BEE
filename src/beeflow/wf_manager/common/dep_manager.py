#!/usr/bin/env python3

import beeflow.common.log as bee_logging
import shutil
import signal
import time
import sys
import os
import subprocess
import getpass
import beeflow.wf_manager.resources.wf_utils as wf_utils
from beeflow.common.config_driver import BeeConfig as bc


dep_log = bee_logging.setup_logging(level='DEBUG')
# gdb_handler = bee_logging.save_log(bee_workdir=bee_workdir,
#        log=dep_log, logfile='gdb_launch.log')


class NoContainerRuntime(Exception):
    pass


def check_container_runtime():
    """
    Checks if the container runtime is currently installed
    """
    # TODO Needs to support singuarity as well
    if shutil.which("ch-convert") is None or shutil.which("ch-run") is None:
        dep_log.error("ch-convert or ch-run not found. Charliecloud required"
                      " for neo4j container.")
        raise NoContainerRuntime('')


def make_dep_dir():
    # Look for a BEE directory in /var/tmp
    bee_workdir = wf_utils.get_bee_workdir()
    bee_dir = f'{bee_workdir}/deps'
    bee_dir_exists = os.path.isdir(bee_dir)
    if not bee_dir_exists:
        os.makedirs(bee_dir)


def get_dep_dir():
    bee_workdir = wf_utils.get_bee_workdir()
    bee_container_dir = f'{bee_workdir}/deps/'
    return bee_container_dir


def get_current_run_dir():
    bee_workdir = wf_utils.get_bee_workdir()
    current_run_dir = f'{bee_workdir}/current_run/'
    return current_run_dir


def get_container_dir():
    container_name = 'dep_container'
    return get_dep_dir() + container_name


def check_container_dir():
    """
    Returns true if the container directory exists
    """
    container_dir = get_container_dir()
    container_dir_exists = os.path.isdir(container_dir)
    return container_dir_exists


def setup_gdb_mounts():
    """
    Sets up mount directories for the graph database
    """

    current_run_dir = get_current_run_dir()
    data_dir = current_run_dir + '/data'
    logs_dir = current_run_dir + '/logs'
    run_dir = current_run_dir + '/run'
    certs_dir = current_run_dir + '/certificates'

    data_dir = os.path.join(data_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    logs_dir = os.path.join(logs_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    run_dir = os.path.join(run_dir, "run")
    os.makedirs(run_dir, exist_ok=True)

    gdb_certs_path = os.path.join(certs_dir, "certificates")
    os.makedirs(gdb_certs_path, exist_ok=True)


def setup_gdb_configs():
    """
        Setup GDB configurations for the next run.
        This function needs to be run before each new invocation since the
        config file could have changed.
    """
    bolt_port = bc.get('graphdb', 'bolt_port')
    http_port = bc.get('graphdb', 'http_port')
    https_port = bc.get('graphdb', 'https_port')

    current_run_dir = get_current_run_dir()
    container_path = get_container_dir()
    confs_dir = os.path.join(current_run_dir, "conf")
    os.makedirs(confs_dir, exist_ok=True)
    gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf",
                                     confs_dir + "/neo4j.conf")
    dep_log.debug(gdb_configfile)

    cfile = open(gdb_configfile, "rt")
    data = cfile.read()
    cfile.close()
    data = data.replace("#dbms.connector.bolt.listen_address=:7687",
                        "dbms.connector.bolt.listen_address=:" + str(bolt_port))
    data = data.replace("#dbms.connector.http.listen_address=:7474",
                        "dbms.connector.http.listen_address=:" + str(http_port))
    data = data.replace("#dbms.connector.https.listen_address=:7473",
                        "dbms.connector.https.listen_address=:" + str(https_port))
    cfile = open(gdb_configfile, "wt")
    cfile.write(data)
    cfile.close()


def create_image():
    """
       Create a new BEE dependency container if one does not exist.
       By default, the container is stored in /tmp/<user>/beeflow/deps.
    """
    # Can throw an exception that needs to be handled by the caller
    check_container_runtime()

    dep_img = bc.get('DEFAULT', 'bee_dep_image')

    # Check for BEE dependency container directory:
    container_dir_exists = check_container_dir()
    if container_dir_exists:
        dep_log.info('Already have neo4j container')
        return
    else:
        make_dep_dir()

    container_dir = get_container_dir()
    # Build new dependency container
    try:
        subprocess.run(["ch-convert", "-i", "tar", "-o", "dir",
                        str(dep_img), str(container_dir)],
                       stdout=sys.stdout, stderr=sys.stderr, check=True)
    except subprocess.CalledProcessError as e:
        dep_log.error(f"ch-convert failed: {e}")
        shutil.rmtree(container_dir)
        dep_log.debug("GraphDB container mount directory " + container_dir + " removed")
        return None

    # Make the certificates directory
    container_certs_path = os.path.join(container_dir, 'var/lib/neo4j/certificates')
    os.makedirs(container_certs_path, exist_ok=True)
    # dep_log.debug('Created certificates directory %s', container_certs_path)


def start_gdb(reexecute=False):
    """
        Start the graph database
    """
    setup_gdb_configs()
    # We need to rerun the mount step before each start
    setup_gdb_mounts()

    db_password = bc.get('graphdb', 'dbpass')
    current_run_dir = get_current_run_dir()
    data_dir = current_run_dir + '/data'
    logs_dir = current_run_dir + '/logs'
    run_dir = current_run_dir + '/run'
    certs_dir = current_run_dir + '/certificates'
    confs_dir = current_run_dir + "/conf"

    container_path = get_container_dir()
    # if not reexecute and len(os.listdir(data_dir)) == 0:
    try:
        command = ['neo4j-admin', 'set-initial-password', str(db_password)]
        proc = subprocess.run([
            "ch-run",
            "--set-env=" + container_path + "/ch/environment",
            "-b", confs_dir + ":/var/lib/neo4j/conf",
            "-b", data_dir + ":/data",
            "-b", logs_dir + ":/logs",
            "-b", run_dir + ":/var/lib/neo4j/run", container_path,
            "--", *command
        ], stdout=sys.stdout, stderr=sys.stderr, check=True)
    except subprocess.CalledProcessError:
        dep_log.error("neo4j-admin set-initial-password failed")
        return None

    try:
        command = ['neo4j', 'start']
        proc = subprocess.Popen([
            "ch-run",
            "--set-env=" + container_path + "/ch/environment",
            "-b",
            confs_dir + ":/var/lib/neo4j/conf",
            "-b",
            data_dir + ":/data",
            "-b",
            logs_dir + ":/logs",
            "-b",
            run_dir + ":/var/lib/neo4j/run",
            "-b",
            certs_dir + ":/var/lib/neo4j/certificates",
            container_path,
            "--", *command
        ], stdout=sys.stdout, stderr=sys.stderr)
    except FileNotFoundError:
        dep_log.error("Neo4j failed to start.")
        return None

    return proc


def wait_gdb(log, gdb_sleep_time=1):

    """
    Need to wait for the GDB. Currently, we're using the sleep time paramater.
    We'd like to remove that in the future.
    """
    log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
    time.sleep(gdb_sleep_time)

def remove_current_run():
    current_run_dir = get_current_run_dir()
    shutil.rmtree(current_run_dir, ignore_errors=True)


def remove_gdb():
    """
    Remove the current GDB bind mount directory
    """
    bee_workdir = wf_utils.get_bee_workdir()
    gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
    old_gdb_workdir = os.path.join(bee_workdir, 'old_gdb')
    if os.path.isdir(gdb_workdir):
        # Rename the directory to guard against NFS errors
        shutil.move(gdb_workdir, old_gdb_workdir)
        time.sleep(2)
        shutil.rmtree(old_gdb_workdir)
        time.sleep(2)


def kill_gdb():
    """
        Kill the current GDB process.
        This will stop functioning correctly with multiple workflow support.
    """
    # TODO TERRIBLE Kludge until we can figure out a better way to get the PID
    user = getpass.getuser()
    ps = subprocess.run([f"ps aux | grep {user} | grep [n]eo4j"], shell=True,
                        stdout=subprocess.PIPE)
    if ps.stdout.decode() != '':
        gdb_pid = int(ps.stdout.decode().split()[1])
        kill_process(gdb_pid)


def kill_process(pid):
    """Kill the process with pid"""
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        dep_log.info('Process already killed')
