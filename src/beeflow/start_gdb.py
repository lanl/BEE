#!/usr/bin/env python3

import beeflow.common.log as bee_logging
import shutil
import tempfile
import sys
import os
import argparse
import subprocess
import getpass
from beeflow.common.config_driver import BeeConfig as bc


def create_pid_file(proc, pid_file, bc):
    """Create a new PID file."""
    os.makedirs(bc.get('DEFAULT','bee_workdir'), exist_ok=True)
    with open('{}/{}'.format(str(bc.get('DEFAULT','bee_workdir')),pid_file), 'w') as fp:
        fp.write(str(proc.pid))

def StartGDB(bc, gdb_workdir, reexecute=False, debug=False):
    """Start the graph database. Returns a Popen process object."""
    bee_workdir = bc.get('DEFAULT','bee_workdir')
    gdb_handler = bee_logging.save_log(bee_workdir=bee_workdir, log=gdb_log, logfile='gdb_launch.log')

    if shutil.which("ch-convert") == None or shutil.which("ch-run") == None:
        gdb_log.error("ch-convert or ch-run not found. Charliecloud required for neo4j container.")
        return None

    # Setup subprocess output
    stdout = sys.stdout
    stderr = sys.stderr

    # Read the config file back in
    db_hostname = bc.get('graphdb','hostname')
    db_password = bc.get('graphdb','dbpass')
    bolt_port   = bc.get('graphdb','bolt_port')
    http_port   = bc.get('graphdb','http_port')
    https_port  = bc.get('graphdb','https_port')
    gdb_img     = bc.get('DEFAULT','bee_dep_image')
    gdb_img_mntdir = bc.get('graphdb','gdb_image_mntdir')

    container_dir = tempfile.mkdtemp(suffix="_" + getpass.getuser(), prefix="gdb_", dir=str(gdb_img_mntdir))
    if debug:
        gdb_log.info("GraphDB container mount directory " + container_dir + " created")

    try:
        image_name = os.path.basename(gdb_img).split('.')[0]
        cp = subprocess.run(["ch-convert", "-i", "tar", "-o", "dir",
                             str(gdb_img), str(container_dir) + f'/{image_name}'],
                             stdout=stdout, stderr=stderr, check=True)
    except subprocess.CalledProcessError as cp:
        gdb_log.error(f"ch-convert failed: {cp}")
        shutil.rmtree(container_dir)
        if debug:
            gdb_log.error("GraphDB container mount directory " + container_dir + " removed")
        return None

    container_path = container_dir + "/" + os.listdir(str(container_dir))[0]
    # Make the certificates directory
    container_certs_path = os.path.join(container_path, 'var/lib/neo4j/certificates')
    os.makedirs(container_certs_path, exist_ok=True)
    if debug:
        gdb_log.info('Created certificates directory %s', container_certs_path)

    gdb_config_path = os.path.join(gdb_workdir, "conf")
    os.makedirs(gdb_config_path, exist_ok=True)
    gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf", gdb_config_path + "/neo4j.conf")
    if debug:
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

    if not reexecute:
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


gdb_log = bee_logging.setup_logging(level='DEBUG')
if not bc.ready():
    bc.init()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gdb_workdir', type=str, required=True)
    parser.add_argument('--reexecute', action='store_true')
    args = parser.parse_args()

    gdb_workdir = args.gdb_workdir
    reexecute = args.reexecute

    proc = StartGDB(bc, gdb_workdir, reexecute)

    if proc is None:
        gdb_log.error('Graph Database failed to start. Exiting.')
        exit()
