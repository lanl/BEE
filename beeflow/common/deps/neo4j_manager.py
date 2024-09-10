"""Contains methods for managing neo4j instance."""
import socket
import os
import shutil
import re
import subprocess
import time

from beeflow.wf_manager.resources import wf_utils
from beeflow.common.db import wfm_db

from beeflow.common import paths
from beeflow.common.deps import container_manager

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging

# Define directories within module scope
bee_workdir = paths.workdir()
mount_dir = os.path.join(bee_workdir, 'gdb_mount')
data_dir = mount_dir + '/data'
logs_dir = mount_dir + '/logs'
run_dir = mount_dir + '/run'
certs_dir = mount_dir + '/certificates'
confs_dir = mount_dir + "/conf"
dags_dir = os.path.join(bee_workdir, 'dags')
graphmls_dir = dags_dir + "/graphmls"
container_path = container_manager.get_container_dir('neo4j')
log = bee_logging.setup('neo4j')


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


def setup_mounts():
    """Set up mount directories for the graph database."""
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(mount_dir, exist_ok=True)
    os.makedirs(certs_dir, exist_ok=True)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(dags_dir, exist_ok=True)
    os.makedirs(graphmls_dir, exist_ok=True)


def setup_configs(bolt_port, http_port, https_port):
    """Set up GDB configuration.

    This function needs to be run before each new invocation since the
    config file could have changed.
    """
    os.makedirs(confs_dir, exist_ok=True)
    gdb_configfile = shutil.copyfile(container_path + "/var/lib/neo4j/conf/neo4j.conf",
                                     confs_dir + "/neo4j.conf")
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

    apoc_configfile = os.path.join(confs_dir, "apoc.conf")
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
            "--set-env=" + container_path + "/ch/environment",
            "--set-env=apoc.export.file.enabled=true",
            "-b", confs_dir + ":/var/lib/neo4j/conf",
            "-b", data_dir + ":/data",
            "-b", logs_dir + ":/logs",
            "-b", run_dir + ":/var/lib/neo4j/run", container_path,
            "-W", "-b", graphmls_dir + ":/var/lib/neo4j/import",
            "--", *command
        ], check=True)
    except subprocess.CalledProcessError:
        log.error("neo4j-admin set-initial-password failed")


def create_database():
    """Create the neo4j database and return the process."""
    try:
        command = ['neo4j', 'console']
        proc = subprocess.Popen([ #noqa can't use with because returning
            "ch-run",
            "--set-env=" + container_path + "/ch/environment",
            "--set-env=apoc.export.file.enabled=true",
            "-b", confs_dir + ":/var/lib/neo4j/conf",
            "-b", data_dir + ":/data",
            "-b", logs_dir + ":/logs",
            "-b", run_dir + ":/var/lib/neo4j/run",
            "-b", certs_dir + ":/var/lib/neo4j/certificates",
            "-W", "-b", graphmls_dir + ":/var/lib/neo4j/import",
            container_path, "--", *command
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        wait_gdb()
        return proc

    except FileNotFoundError:
        log.error("Neo4j failed to start.")
        return -1


def start():
    """Start the graph database."""
    log.info('Starting Neo4j Database')

    bolt_port, http_port, https_port = setup_ports()

    setup_configs(bolt_port, http_port, https_port)

    setup_mounts()

    create_credentials()

    return create_database()


def wait_gdb():
    """Need to wait for the GDB. Currently, we're using the sleep time paramater.

    We'd like to remove that in the future.
    """
    gdb_sleep_time = bc.get('graphdb', 'sleep_time')
    print(f'waiting {gdb_sleep_time}s for GDB to come up')
    time.sleep(gdb_sleep_time)


def remove_gdb():
    """Remove the current GDB bind mount directory."""
    gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
    old_gdb_workdir = os.path.join(bee_workdir, 'old_gdb')
    if os.path.isdir(gdb_workdir):
        # Rename the directory to guard against NFS errors
        shutil.move(gdb_workdir, old_gdb_workdir)
        time.sleep(2)
        shutil.rmtree(old_gdb_workdir)
        time.sleep(2)
