"""Utility functions for wf_manager resources."""

import os
import shutil
import requests
import jsonpickle

from beeflow.common import log as bee_logging
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.gdb import neo4j_driver
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.connection import Connection
from beeflow.common import paths
from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db

from celery import shared_task #noqa (pylama can't find celery imports)

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

    # bolt_port = db.info.get_bolt_port()
    # return get_workflow_interface_by_bolt_port(wf_id, bolt_port)
    driver = neo4j_driver.Neo4jDriver()
    bolt_port = db.info.get_port('bolt')
    if bolt_port != -1:
        connect_neo4j_driver(bolt_port)
    wfi = WorkflowInterface(wf_id, driver)
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


def schedule_submit_tasks(wf_id, tasks):
    """Schedule and then submit tasks to the TM."""
    # Submit ready tasks to the scheduler
    allocation = submit_tasks_scheduler(tasks)  #NOQA
    # Submit tasks to TM
    submit_tasks_tm(wf_id, tasks, allocation)


def connect_neo4j_driver(bolt_port):
    """Create a neo4j driver to a gdb through bolt port."""
    driver = neo4j_driver.Neo4jDriver()
    driver.connect(user="neo4j", bolt_port=bolt_port,
                   db_hostname=bc.get("graphdb", "hostname"),
                   password=bc.get("graphdb", "dbpass"))
    driver.create_bee_node()


def setup_workflow(wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow=None,
                   tasks=None, reexecute=False):
    """Initialize Workflow in Separate Process."""
    wfi = get_workflow_interface(wf_id)
    if reexecute:
        wfi.reset_workflow(wf_id)
    else:
        wfi.initialize_workflow(workflow)

    log.info('Setting workflow metadata')
    create_wf_metadata(wf_id, wf_name)
    db = connect_db(wfm_db, get_db_path())
    if reexecute:
        _, tasks = wfi.get_workflow()
        # Tasks come in backwards
        tasks.reverse()
    for task in tasks:
        if not reexecute:
            wfi.add_task(task)
        metadata = wfi.get_task_metadata(task)
        metadata['workdir'] = wf_workdir
        wfi.set_task_metadata(task, metadata)
        db.workflows.add_task(task.id, wf_id, task.name, "WAITING")

    update_wf_status(wf_id, 'Waiting')
    db.workflows.update_workflow_state(wf_id, 'Waiting')
    if no_start:
        log.info('Not starting workflow, as requested')
    else:
        log.info('Starting workflow')
        db.workflows.update_workflow_state(wf_id, 'Running')
        start_workflow(wf_id)


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
