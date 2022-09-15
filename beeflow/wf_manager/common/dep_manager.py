#!/usr/bin/env python3

"""Functions for managing the BEE depency container and associated bind mounts."""

import os
import sys
import time
import shutil
import signal
import stat
import subprocess
import getpass

import beeflow.common.log as bee_logging
from beeflow.wf_manager.resources import wf_utils
from beeflow.common.config_driver import BeeConfig as bc


dep_log = bee_logging.setup_logging(level='DEBUG')


class NoContainerRuntime(Exception):
    """An exception for no container runtime like charliecloud or singularity."""


def check_container_runtime():
    """Check if the container runtime is currently installed."""
    # Needs to support singuarity as well
    if shutil.which("ch-convert") is None or shutil.which("ch-run") is None:
        dep_log.error("ch-convert or ch-run not found. Charliecloud required"
                      " for neo4j container.")
        raise NoContainerRuntime('')


def make_dep_dir():
    """Make a new bee dependency container directory."""
    bee_workdir = wf_utils.get_bee_workdir()
    bee_dir = f'{bee_workdir}/deps'
    bee_dir_exists = os.path.isdir(bee_dir)
    if not bee_dir_exists:
        os.makedirs(bee_dir)


def get_dep_dir():
    """Return the dependency directory path."""
    bee_workdir = wf_utils.get_bee_workdir()
    bee_container_dir = f'{bee_workdir}/deps/'
    return bee_container_dir


def get_current_run_dir():
    """Return the current run directory."""
    bee_workdir = wf_utils.get_bee_workdir()
    current_run_dir = f'{bee_workdir}/current_run/'
    return current_run_dir


def get_container_dir():
    """Return the depency container path."""
    container_name = 'dep_container'
    return get_dep_dir() + container_name


def check_container_dir():
    """Return true if the container directory exists."""
    container_dir = get_container_dir()
    container_dir_exists = os.path.isdir(container_dir)
    return container_dir_exists


def setup_gdb_mounts():
    """Set up mount directories for the graph database."""
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
    """Set up GDB configuration.

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

    with open(gdb_configfile, "rt", encoding="utf8") as cfile:
        data = cfile.read()

    data = data.replace("#dbms.connector.bolt.listen_address=:7687",
                        "dbms.connector.bolt.listen_address=:" + str(bolt_port))
    data = data.replace("#dbms.connector.http.listen_address=:7474",
                        "dbms.connector.http.listen_address=:" + str(http_port))
    data = data.replace("#dbms.connector.https.listen_address=:7473",
                        "dbms.connector.https.listen_address=:" + str(https_port))
    with open(gdb_configfile, "wt", encoding="utf8") as cfile:
        cfile.write(data)


def create_image():
    """Create a new BEE dependency container if one does not exist.

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

    make_dep_dir()
    container_dir = get_container_dir()
    # Build new dependency container
    try:
        subprocess.run(["ch-convert", "-i", "tar", "-o", "dir",
                        str(dep_img), str(container_dir)],
                       stdout=sys.stdout, stderr=sys.stderr, check=True)
    except subprocess.CalledProcessError as error:
        dep_log.error(f"ch-convert failed: {error}")
        shutil.rmtree(container_dir)
        dep_log.debug(f"GraphDB container mount directory {container_dir} removed")
        return

    # Make the certificates directory
    container_certs_path = os.path.join(container_dir, 'var/lib/neo4j/certificates')
    os.makedirs(container_certs_path, exist_ok=True)


def start_gdb(reexecute=False):
    """Start the graph database."""
    setup_gdb_configs()
    # We need to rerun the mount step before each start
    if not reexecute:
        setup_gdb_mounts()

    db_password = bc.get('graphdb', 'dbpass')
    current_run_dir = get_current_run_dir()
    data_dir = current_run_dir + '/data'
    logs_dir = current_run_dir + '/logs'
    run_dir = current_run_dir + '/run'
    certs_dir = current_run_dir + '/certificates'
    confs_dir = current_run_dir + "/conf"

    container_path = get_container_dir()
    if not reexecute:
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
        with subprocess.Popen([
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
        ], stdout=sys.stdout, stderr=sys.stderr) as proc:
            return proc
    except FileNotFoundError:
        dep_log.error("Neo4j failed to start.")
        return None


def wait_gdb(log, gdb_sleep_time=1):
    """Need to wait for the GDB. Currently, we're using the sleep time paramater.

    We'd like to remove that in the future.
    """
    log.info(f'waiting {gdb_sleep_time}s for GDB to come up')
    time.sleep(gdb_sleep_time)


def rm_dir_readonly(func, path, _):
    """Remove directory with read-only files."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_current_run():
    """Remove the current run directory."""
    current_run_dir = get_current_run_dir()
    if os.path.exists(current_run_dir):
        shutil.rmtree(current_run_dir, onerror=rm_dir_readonly)


def remove_gdb():
    """Remove the current GDB bind mount directory."""
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
    """Kill the current GDB process.

    This will stop functioning correctly with multiple workflow support.
    """
    # TERRIBLE Kludge until we can figure out a better way to get the PID
    user = getpass.getuser()
    process = subprocess.run([f"ps aux | grep {user} | grep [n]eo4j"], shell=True,
                             stdout=subprocess.PIPE, check=False)
    if process.stdout.decode() != '':
        gdb_pid = int(process.stdout.decode().split()[1])
        kill_process(gdb_pid)


def kill_process(pid):
    """Kill the process with pid."""
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        dep_log.info('Process already killed')
