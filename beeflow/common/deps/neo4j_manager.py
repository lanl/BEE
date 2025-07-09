"""Contains methods for managing neo4j instance."""
import socket
import os
import shutil
import re
import subprocess
import time
import logging

from neo4j import GraphDatabase
from neo4j import exceptions as neo4j_exc

from beeflow.common.gdb.neo4j_driver import (DEFAULT_USER, DEFAULT_PASSWORD, DEFAULT_HOSTNAME,
                                             DEFAULT_BOLT_PORT, MAX_WAIT_SECS, RETRY_DELAY_SECS)

from beeflow.wf_manager.resources import wf_utils
from beeflow.common.db import wfm_db

from beeflow.common import paths
from beeflow.common.deps import container_manager

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging


BEE_WORKDIR = None
MOUNT_DIR = None
DATA_DIR = None
LOGS_DIR = None
RUN_DIR = None
CERTS_DIR = None
CONFS_DIR = None
GRAPHMLS_DIR = None
CONTAINER_PATH = None

log = None  # pylint: disable=C0103

def get_open_port():
    """Return an open ephemeral port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def setup_ports():
    """Return three open ports for bolt, http, https."""
    # Get ports for neo4j to run
    bolt_port = get_open_port()
    http_port = get_open_port()
    https_port = get_open_port()

    db = wf_utils.connect_db(wfm_db, wf_utils.get_db_path())

    db.info.set_port('bolt', bolt_port)
    db.info.set_port('http', http_port)
    db.info.set_port('https', https_port)
    return bolt_port, http_port, https_port


def define_directories():
    """Define directories within module scope."""
    global BEE_WORKDIR, MOUNT_DIR, DATA_DIR, LOGS_DIR, RUN_DIR, \
        CERTS_DIR, CONFS_DIR, GRAPHMLS_DIR, CONTAINER_PATH
    BEE_WORKDIR = paths.workdir()
    MOUNT_DIR = os.path.join(BEE_WORKDIR, 'gdb_mount')
    DATA_DIR = MOUNT_DIR + '/data'
    LOGS_DIR = MOUNT_DIR + '/logs'
    RUN_DIR = MOUNT_DIR + '/run'
    CERTS_DIR = MOUNT_DIR + '/certificates'
    CONFS_DIR = MOUNT_DIR + "/conf"
    GRAPHMLS_DIR = MOUNT_DIR + '/graphmls'
    CONTAINER_PATH = container_manager.get_container_dir('neo4j')


def setup_mounts():
    """Set up mount directories for the graph database."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(MOUNT_DIR, exist_ok=True)
    os.makedirs(CERTS_DIR, exist_ok=True)
    os.makedirs(RUN_DIR, exist_ok=True)
    os.makedirs(GRAPHMLS_DIR, exist_ok=True)


def setup_configs(bolt_port, http_port, https_port):
    """Set up GDB configuration.

    This function needs to be run before each new invocation since the
    config file could have changed.
    """
    os.makedirs(CONFS_DIR, exist_ok=True)
    gdb_configfile = shutil.copyfile(CONTAINER_PATH + "/var/lib/neo4j/conf/neo4j.conf",
                                     CONFS_DIR + "/neo4j.conf")
    log.info(gdb_configfile)

    with open(gdb_configfile, "rt", encoding="utf8") as cfile:
        data = cfile.read()

    log.info(f"new bolt: {bolt_port}")
    bolt_config = r'#(server.bolt.listen_address=):[0-9]*'
    data = re.sub(bolt_config, rf'\1:{bolt_port}', data)
    http_config = r'#(server.http.listen_address=):[0-9]*'
    data = re.sub(http_config, rf'\1:{http_port}', data)
    https_config = r'#(server.https.listen_address=):[0-9]*'
    data = re.sub(https_config, rf'\1:{https_port}', data)

    with open(gdb_configfile, "wt", encoding="utf8") as cfile:
        cfile.write(data)

    apoc_configfile = os.path.join(CONFS_DIR, "apoc.conf")
    if not os.path.exists(apoc_configfile):
        with open(apoc_configfile, "wt", encoding="utf8") as afile:
            afile.write("apoc.export.file.enabled=true\n")
        log.info(f"Created {apoc_configfile} with apoc.export.file.enabled=true")
    else:
        with open(apoc_configfile, "rt", encoding="utf8") as afile:
            apoc_data = afile.read()

        apoc_config = r'#?(apoc.export.file.enabled=)[^\n]*'
        if re.search(apoc_config, apoc_data):
            apoc_data = re.sub(apoc_config, r'apoc.export.file.enabled=true', apoc_data)
        else:
            apoc_data += "\napoc.export.file.enabled=true\n"

        with open(apoc_configfile, "wt", encoding="utf8") as afile:
            afile.write(apoc_data)


def create_credentials():
    """Create the password and set the logfiles in environment."""
    db_password = bc.get('graphdb', 'dbpass')
    try:
        command = ['neo4j-admin', 'dbms', 'set-initial-password', str(db_password)]
        subprocess.run([
            "ch-run",
            "--set-env=" + CONTAINER_PATH + "/ch/environment",
            "--set-env=apoc.export.file.enabled=true",
            "-b", CONFS_DIR + ":/var/lib/neo4j/conf",
            "-b", DATA_DIR + ":/data",
            "-b", LOGS_DIR + ":/logs",
            "-b", RUN_DIR + ":/var/lib/neo4j/run", CONTAINER_PATH,
            "-W", "-b", GRAPHMLS_DIR + ":/var/lib/neo4j/import",
            "--", *command
        ], check=True)
    except subprocess.CalledProcessError:
        log.error("neo4j-admin set-initial-password failed")


def create_database(bolt_port):
    """Create the neo4j database and return the process."""
    try:
        command = ['neo4j', 'console']
        proc = subprocess.Popen([ # pylint: disable=R1732 # can't use with because returning
            "ch-run",
            "--set-env=" + CONTAINER_PATH + "/ch/environment",
            "--set-env=apoc.export.file.enabled=true",
            "-b", CONFS_DIR + ":/var/lib/neo4j/conf",
            "-b", DATA_DIR + ":/data",
            "-b", LOGS_DIR + ":/logs",
            "-b", RUN_DIR + ":/var/lib/neo4j/run",
            "-b", CERTS_DIR + ":/var/lib/neo4j/certificates",
            "-W", "-b", GRAPHMLS_DIR + ":/var/lib/neo4j/import",
            CONTAINER_PATH, "--", *command
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wait_gdb(bolt_port=bolt_port, user="neo4j", password=bc.get('graphdb', 'dbpass'),
                 hostname=bc.get('graphdb', 'hostname'))
        return proc

    except FileNotFoundError:
        log.error("Neo4j failed to start.")
        return -1


def start():
    """Start the graph database."""

    global log
    log = bee_logging.setup("neo4j")
    log.setLevel(logging.INFO)
    log.propagate = False

    log.info('Starting Neo4j Database')

    bolt_port, http_port, https_port = setup_ports()

    define_directories()

    setup_configs(bolt_port, http_port, https_port)

    setup_mounts()

    create_credentials()

    return create_database(bolt_port=bolt_port)


def wait_gdb(bolt_port=DEFAULT_BOLT_PORT, user=DEFAULT_USER, password=DEFAULT_PASSWORD, **kwargs):
    """
    Block until the Neo4j instance answers a Bolt handshake
    or raise RuntimeError after MAX_WAIT_SECS.
    """
    db_hostname = kwargs.get("db_hostname", DEFAULT_HOSTNAME)
    uri = f"bolt://{db_hostname}:{bolt_port}"
    start_time = time.monotonic()

    while True:
        try:
            with GraphDatabase.driver(uri, auth=(user, password)) as driver:
                driver.verify_connectivity()      # asks server for a tiny query
            # Success → database is ready
            log.info("Neo4j is up and responding")
            return
        except (neo4j_exc.ServiceUnavailable,
                neo4j_exc.DriverError):
            elapsed = time.monotonic() - start_time
            if elapsed >= MAX_WAIT_SECS:
                log.info("Max wait time elapsed")
                return
            log.info(f"Waiting {RETRY_DELAY_SECS} seconds for Neo4j to become ready...")
            time.sleep(RETRY_DELAY_SECS)


def remove_gdb():
    """Remove the current GDB bind mount directory."""
    gdb_workdir = os.path.join(BEE_WORKDIR, 'current_gdb')
    old_gdb_workdir = os.path.join(BEE_WORKDIR, 'old_gdb')
    if os.path.isdir(gdb_workdir):
        # Rename the directory to guard against NFS errors
        shutil.move(gdb_workdir, old_gdb_workdir)
        time.sleep(2)
        shutil.rmtree(old_gdb_workdir)
        time.sleep(2)
