"""Utility functions for wf_manager resources."""

import os
import shutil
import socket
import time
import requests
import jsonpickle

from beeflow.common import log as bee_logging
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.gdb_interface import GraphDatabaseInterface
from beeflow.common.gdb import neo4j_driver
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.wf_manager.common import dep_manager
from beeflow.common.connection import Connection
from beeflow.common import paths
from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db

log = bee_logging.setup(__name__)


def get_db_path():
    """Return db name."""
    db_name = 'wfm.db'
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    db_path = bee_workdir + '/' + db_name
    return db_path


def get_bee_workdir():
    """Get the bee workflow directory from the configuration file."""
    return bc.get('DEFAULT', 'bee_workdir')


def get_workflows_dir():
    """Get the workflows script directory from beeflow."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows')
    return workflows_dir


def get_workflow_dir(wf_id):
    """Get the workflow script dir for a particular workflow."""
    return os.path.join(get_workflows_dir(), wf_id)


def create_workflow_dir(wf_id):
    """Create the workflows directory."""
    os.makedirs(get_workflow_dir(wf_id))


def create_current_run_dir():
    """Create directory to store current run GDB bind info."""
    bee_workdir = get_bee_workdir()
    current_run_dir = os.path.join(bee_workdir, 'current_run')
    os.makedirs(current_run_dir)


def remove_current_run_dir():
    """Remove current run directory."""
    bee_workdir = get_bee_workdir()
    current_run_dir = os.path.join(bee_workdir, 'current_run')
    if os.path.exists(current_run_dir):
        shutil.rmtree(current_run_dir)


def remove_wf_dir(wf_id):
    """Remove a workflow directory."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    if os.path.exists(workflows_dir):
        shutil.rmtree(workflows_dir)


def create_wf_metadata(wf_id, wf_name):
    """Create workflow metadata files."""
    create_wf_name(wf_id, wf_name)
    create_wf_status(wf_id)


def create_wf_name(wf_id, wf_name):
    """Create workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    name_path = os.path.join(workflows_dir, 'bee_wf_name')
    with open(name_path, 'w', encoding="utf8") as name:
        name.write(wf_name)


def create_wf_status(wf_id):
    """Create workflow status metadata file."""
    update_wf_status(wf_id, 'Pending')


def update_wf_status(wf_id, status_msg):
    """Update workflow status metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    status_path = os.path.join(workflows_dir, 'bee_wf_status')
    with open(status_path, 'w', encoding="utf8") as status:
        status.write(status_msg)


def read_wf_status(wf_id):
    """Read workflow status metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    status_path = os.path.join(workflows_dir, 'bee_wf_status')
    with open(status_path, 'r', encoding="utf8") as status:
        wf_status = status.readline()
    return wf_status


def read_wf_name(wf_id):
    """Read workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    status_path = os.path.join(workflows_dir, 'bee_wf_name')
    with open(status_path, 'r', encoding="utf8") as status:
        wf_name = status.readline()
    return wf_name


def create_wf_namefile(wf_name, wf_id):
    """Create workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, 'workflows', wf_id)
    name_path = os.path.join(workflows_dir, 'bee_wf_name')
    with open(name_path, 'w', encoding="utf8") as name:
        name.write(wf_name)


def get_workflow_interface(wf_id):
    """Instantiate and return workflow interface object."""
    db = connect_db(wfm_db, get_db_path())
    # Wait for the GDB
    if db.workflows.get_workflow_state(wf_id) == 'Initializing':
        raise RuntimeError('Workflow is still initializing')
    bolt_port = db.workflows.get_bolt_port(wf_id)
    return get_workflow_interface_by_bolt_port(wf_id, bolt_port)


def get_workflow_interface_by_bolt_port(wf_id, bolt_port):
    """Return a workflow interface connection using just the bolt port."""
    try:
        driver = neo4j_driver.Neo4jDriver(user="neo4j", bolt_port=bolt_port,
                                          db_hostname=bc.get("graphdb", "hostname"),
                                          password=bc.get("graphdb", "dbpass"))
        iface = GraphDatabaseInterface(driver)
        wfi = WorkflowInterface(iface)
    except neo4j_driver.Neo4jNotRunning:
        log.info("Neo4j Appears to be Down")
        # There are several possibilities here
        # First check if the GDB is up
        db = connect_db(wfm_db, get_db_path())
        gdb_pid = db.workflows.get_gdb_pid(wf_id)
        try:
            # Not actually killing the GDB just checking if the PID is up
            # Returns an exception if the GDB is running
            os.kill(gdb_pid, 0)
            # The GDB process is running so we'll kill it and restart it
        except ProcessLookupError:
            log.error('The GDB is currently down restarting it')
            http_port = db.workflows.get_http_port(wf_id)
            https_port = db.workflows.get_https_port(wf_id)
            run_dir = db.workflows.get_run_dir(wf_id)
            gdb_pid = dep_manager.start_gdb(run_dir, bolt_port, http_port, https_port,
                                            reexecute=True)
            time.sleep(10)
            db.workflows.update_gdb_pid(wf_id, gdb_pid)
            driver = neo4j_driver.Neo4jDriver(user="neo4j", bolt_port=bolt_port,
                                              db_hostname=bc.get("graphdb", "hostname"),
                                              password=bc.get("graphdb", "dbpass"))
            iface = GraphDatabaseInterface(driver)
            wfi = WorkflowInterface(iface)
            wfi.get_workflow()
        except PermissionError:
            # Something has gone wrong. The user has no perms for their gdb.
            # Just note a fatal error and exit
            log.error('Perms error for GDB. Please report this to BEE developers.')
    return wfi


def tm_url():
    """Get Task Manager url."""
    # tm_listen_port = bc.get('task_manager', 'listen_port')
    db = connect_db(wfm_db, get_db_path())
    tm_listen_port = db.info.get_port('tm')
    task_manager = "bee_tm/v1/task/"
    return f'http://127.0.0.1:{tm_listen_port}/{task_manager}'


# Base URLs for the TM and the Scheduler
TM_URL = "bee_tm/v1/task/"
SCHED_URL = "bee_sched/v1/"


def _connect_tm():
    """Return a connection to the TM."""
    return Connection(paths.tm_socket())


def sched_url():
    """Get Scheduler url."""
    db = connect_db(wfm_db, get_db_path())
    scheduler = "bee_sched/v1/"
    # sched_listen_port = bc.get('scheduler', 'listen_port')
    sched_listen_port = db.info.get_port('sched')
    return f'http://127.0.0.1:{sched_listen_port}/{scheduler}'


def _connect_scheduler():
    """Return a connection to the Scheduler."""
    return Connection(paths.sched_socket())


def _resource(component, tag=""):
    """Access Task Manager or Scheduler."""
    if component == "tm":
        url = TM_URL + str(tag)
    elif component == "sched":
        url = SCHED_URL + str(tag)
    return url


# Submit tasks to the TM
# pylama:ignore=W0613
def submit_tasks_tm(wf_id, tasks, allocation):
    """Submit a task to the task manager."""
    wfi = get_workflow_interface(wf_id)
    for task in tasks:
        metadata = wfi.get_task_metadata(task)
        task.workdir = metadata['workdir']
    # Serialize task with json
    tasks_json = jsonpickle.encode(tasks)
    # Send task_msg to task manager
    names = [task.name for task in tasks]
    log.info(f"Submitted {names} to Task Manager")
    try:
        conn = _connect_tm()
        resp = conn.post(_resource('tm', "submit/"), json={'tasks': tasks_json},
                         timeout=5)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to task manager to submit tasks.')
        return

    if resp.status_code != 200:
        log.info(f"Submit task to TM returned bad status: {resp.status_code}")


def tasks_to_sched(tasks):
    """Convert gdb tasks to sched tasks."""
    sched_tasks = []
    for task in tasks:
        sched_task = {
            'workflow_name': 'workflow',
            'task_name': task.name,
            'requirements': {
                'max_runtime': 1,
                'nodes': 1
            }
        }
        sched_tasks.append(sched_task)
    return sched_tasks


def submit_tasks_scheduler(tasks):
    """Submit a list of tasks to the scheduler."""
    sched_tasks = tasks_to_sched(tasks)
    # The workflow name will eventually be added to the wfi workflow object
    try:
        conn = _connect_scheduler()
        resp = conn.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks,
                        timeout=5)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to scheduler to submit tasks.')
        return "Did not work"

    if resp.status_code != 200:
        log.info(f"Something bad happened {resp.status_code}")
        return "Did not work"
    return resp.json()


def get_open_port():
    """Return an open ephemeral port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def schedule_submit_tasks(wf_id, tasks):
    """Schedule and then submit tasks to the TM."""
    # Submit ready tasks to the scheduler
    allocation = submit_tasks_scheduler(tasks)  #NOQA
    # Submit tasks to TM
    submit_tasks_tm(wf_id, tasks, allocation)


def start_workflow(wf_id):
    """Attempt to start the workflow, returning True if successful."""
    db = connect_db(wfm_db, get_db_path())
    wfi = get_workflow_interface(wf_id)
    state = wfi.get_workflow_state()
    if state in ('RUNNING', 'PAUSED', 'COMPLETED'):
        return False
    wfi.execute_workflow()
    tasks = wfi.get_ready_tasks()
    schedule_submit_tasks(wf_id, tasks)
    wf_id = wfi.workflow_id
    update_wf_status(wf_id, 'Running')
    db.workflows.update_workflow_state(wf_id, 'Running')
    return True
