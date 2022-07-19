#!/usr/bin/env python3

import beeflow.common.log as bee_logging
import shutil
import tempfile
import sys
import os
import argparse
import subprocess
import getpass
from beeflow.common.config_driver import BeeConfig


def create_pid_file(proc, pid_file, bc):
    """Create a new PID file."""
    os.makedirs(bc.userconfig.get('DEFAULT','bee_workdir'), exist_ok=True)
    with open('{}/{}'.format(str(bc.userconfig.get('DEFAULT','bee_workdir')),pid_file), 'w') as fp:
        fp.write(str(proc.pid))

def check_container_runtime():
    if shutil.which("ch-convert") == None or shutil.which("ch-run") == None:
        gdb_log.error("ch-convert or ch-run not found. Charliecloud required for neo4j container.")
        return None

def check_bee_container_dir():
    bee_container_dir = get_bee_container_dir()

def get_bee_dir():
    username = getpass.getuser()
    bee_container_dir = f'/tmp/{username}/beeflow/'
    return bee_container_dir

def make_bee_dir():
    # Look for a BEE directory in /var/tmp
    username = getpass.getuser()
    bee_dir = f'/tmp/{username}/beeflow/' 
    bee_dir_exists = os.path.isdir(bee_dir)
    if not bee_dir_exists:
        os.makedirs(bee_dir)

def check_container_dir():
    bee_dir = get_bee_dir()
    bee_dir_exists = os.path.isdir(bee_dir)
   

def start_gdb(gdb_workdir, reexecute=False):
    """Start the graph database. Returns a Popen process object."""
    #--GetBeeWorkdir
    bc = BeeConfig()
    bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
    #--SetupLogging
    gdb_handler = bee_logging.save_log(bee_workdir=bee_workdir, log=gdb_log, logfile='gdb_launch.log')

    #--CheckContainerRuntime
    check_container_runtime()

    #--ReadGraphDBConfig
    db_hostname = bc.userconfig.get('graphdb','hostname')
    db_password = bc.userconfig.get('graphdb','dbpass')
    bolt_port   = bc.userconfig.get('graphdb','bolt_port')
    http_port   = bc.userconfig.get('graphdb','http_port')
    https_port  = bc.userconfig.get('graphdb','https_port')
    gdb_img     = bc.userconfig.get('graphdb','gdb_image')
    gdb_img_mntdir = bc.userconfig.get('graphdb','gdb_image_mntdir')

    #--CreateTmpDirectory
    # Make bee container directory if it doesn't exist
    make_bee_dir()
    
    # Check for container directory:
    container_dir_exists = check_container_dir()
    #container_dir = tempfile.mkdtemp(suffix="_" + getpass.getuser(), prefix="gdb_", dir=str(gdb_img_mntdir))
    container
    if container_dir_exists:
        log.info('Already have neo4j container')
        return
    #gdb_log.debug("GraphDB container mount directory " + container_dir + " created")

    #--CreateBaseImage
    # Create neo4j container
    
    try:
        image_name = os.path.basename(gdb_img).split('.')[0]
        cp = subprocess.run(["ch-convert", "-i", "tar", "-o", "dir",
                             str(gdb_img), str(container_dir) + f'/{image_name}'],
                             stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError as cp:
        gdb_log.error(f"ch-convert failed: {cp}")
        shutil.rmtree(container_dir)
        gdb_log.debug("GraphDB container mount directory " + container_dir + " removed")
        return None

    #--GetContainerPath
    container_path = container_dir + "/" + os.listdir(str(container_dir))[0]
    #--SetupCertificates
    # Make the certificates directory
    container_certs_path = os.path.join(container_path, 'var/lib/neo4j/certificates')
    os.makedirs(container_certs_path, exist_ok=True)
    gdb_log.debug('Created certificates directory %s', container_certs_path)

    #--SetupConfigs
    gdb_config_path = os.path.join(gdb_workdir, "conf")
    os.makedirs(gdb_config_path, exist_ok=True)
    gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf", gdb_config_path + "/neo4j.conf")
    gdb_log.debug(gdb_configfile)

    cfile = open(gdb_configfile, "rt")
    data = cfile.read()
    cfile.close()
    data = data.replace("#dbms.connector.bolt.listen_address=:7687", "dbms.connector.bolt.listen_address=:" + str(bolt_port))
    data = data.replace("#dbms.connector.http.listen_address=:7474", "dbms.connector.http.listen_address=:" + str(http_port))
    data = data.replace("#dbms.connector.https.listen_address=:7473", "dbms.connector.https.listen_address=:" + str(https_port))
    cfile = open(gdb_configfile, "wt")
    cfile.write(data)
    cfile.close()

    #--SetupMntDirs
    gdb_data_path = os.path.join(gdb_workdir, "data")
    os.makedirs(gdb_data_path, exist_ok=True)

    gdb_log_path = os.path.join(gdb_workdir, "logs")
    os.makedirs(gdb_log_path, exist_ok=True)

    gdb_run_path = os.path.join(gdb_workdir, "run")
    os.makedirs(gdb_run_path, exist_ok=True)

    gdb_certs_path = os.path.join(gdb_workdir, "certificates")
    os.makedirs(gdb_certs_path, exist_ok=True)

    #--StartUpGDB
    if not reexecute:
        command = ['neo4j-admin', 'set-initial-password', str(db_password)]
    else:
        command = ['neo4j', 'start']

    try:

        # Verify we're actually using the certificates
        proc = subprocess.run([
            "ch-run",
            "--set-env=" + container_path + "/ch/environment",
            "-b", gdb_config_path + ":/var/lib/neo4j/conf",
            "-b", gdb_data_path + ":/data",
            "-b", gdb_log_path + ":/logs",
            "-b", gdb_run_path + ":/var/lib/neo4j/run", container_path,
            "--", command
        ], stdout=sys.stdout, stderr=sys.stderr, check=True)
    except subprocess.CalledProcessError as cp:
        gdb_log.error("neo4j-admin set-initial-password failed")
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


gdb_log = bee_logging.setup_logging(level='DEBUG')

#--main
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gdb_workdir', type=str, required=True)
    parser.add_argument('--reexecute', action='store_true')
    args = parser.parse_args()

    gdb_workdir = args.gdb_workdir
    reexecute = args.reexecute

    proc = start_gdb(gdb_workdir, reexecute)

    if proc is None:
        gdb_log.error('Graph Database failed to start. Exiting.')
        exit()
