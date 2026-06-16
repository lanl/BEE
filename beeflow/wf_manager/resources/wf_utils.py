"""Utility functions for wf_manager resources."""

from datetime import datetime as dt
import os
import shutil
import pathlib
import requests
from celery import shared_task

from beeflow.common import log as bee_logging
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.gdb import neo4j_driver, sqlite3_driver
from beeflow.common.gdb.generate_graph import generate_viz
from beeflow.common.gdb.graphml_key_updater import update_graphml
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.connection import Connection
from beeflow.common import paths
from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db
from beeflow.task_manager.models import SubmitTasksRequest
from beeflow.common.deps.neo4j_manager import connect_neo4j_driver


log = bee_logging.setup(__name__)


def get_db_path():
    """Return db name."""
    db_name = "wfm.db"
    bee_workdir = bc.get("DEFAULT", "bee_workdir")
    db_path = bee_workdir + "/" + db_name
    return db_path


def get_bee_workdir():
    """Get the bee workflow directory from the configuration file."""
    return bc.get("DEFAULT", "bee_workdir")


def get_workflows_dir():
    """Get the workflows script directory from beeflow."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, "workflows")
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
    current_run_dir = os.path.join(bee_workdir, "current_run")
    os.makedirs(current_run_dir)


def remove_current_run_dir():
    """Remove current run directory."""
    bee_workdir = get_bee_workdir()
    current_run_dir = os.path.join(bee_workdir, "current_run")
    if os.path.exists(current_run_dir):
        shutil.rmtree(current_run_dir)


def remove_wf_dir(wf_id):
    """Remove a workflow directory."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, "workflows", wf_id)
    if os.path.exists(workflows_dir):
        shutil.rmtree(workflows_dir)


def create_wf_metadata(wf_id, wf_name):
    """Create workflow metadata files."""
    create_wf_name(wf_id, wf_name)
    create_wf_status(wf_id)


def create_wf_name(wf_id, wf_name):
    """Create workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, "workflows", wf_id)
    name_path = os.path.join(workflows_dir, "bee_wf_name")
    with open(name_path, "w", encoding="utf8") as name:
        name.write(wf_name)


def create_wf_status(wf_id):
    """Create workflow status metadata file."""
    update_wf_status(wf_id, "Pending")


def update_wf_status(wf_id, status_msg):
    """Update workflow status"""
    wfi = get_workflow_interface(wf_id)
    wfi.set_workflow_state(status_msg)


def get_wf_status(wf_id):
    """Read workflow status metadata file."""
    wfi = get_workflow_interface(wf_id)
    try:
        state = wfi.get_workflow_state()
        return state
    except AttributeError:
        log.info(f"Workflow {wf_id} not found in the database.")
        return None


def read_wf_name(wf_id):
    """Read workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, "workflows", wf_id)
    status_path = os.path.join(workflows_dir, "bee_wf_name")
    with open(status_path, "r", encoding="utf8") as status:
        wf_name = status.readline()
    return wf_name


def create_wf_namefile(wf_name, wf_id):
    """Create workflow name metadata file."""
    bee_workdir = get_bee_workdir()
    workflows_dir = os.path.join(bee_workdir, "workflows", wf_id)
    name_path = os.path.join(workflows_dir, "bee_wf_name")
    with open(name_path, "w", encoding="utf8") as name:
        name.write(wf_name)


def get_workflow_interface(wf_id):
    """Instantiate and return workflow interface object."""

    # Wait for the GDB

    # bolt_port = db.info.get_bolt_port()
    # return get_workflow_interface_by_bolt_port(wf_id, bolt_port)
    if bc.get('graphdb','type').lower() == 'sqlite3':
        driver = sqlite3_driver.SQLDriver()
        driver.connect()
    else:
        db = connect_db(wfm_db, get_db_path())
        driver = neo4j_driver.Neo4jDriver()
        bolt_port = db.info.get_port("bolt")
        if bolt_port != -1:
            connect_neo4j_driver(bolt_port)
    wfi = WorkflowInterface(wf_id, driver)
    return wfi


def tm_url():
    """Get Task Manager url."""
    # tm_listen_port = bc.get('task_manager', 'listen_port')
    db = connect_db(wfm_db, get_db_path())
    tm_listen_port = db.info.get_port("tm")
    task_manager = "bee_tm/v1/task/"
    return f"http://127.0.0.1:{tm_listen_port}/{task_manager}"


# Base URLs for the TM and the Scheduler
TM_URL = "bee_tm/v1/task/"


def _connect_tm():
    """Return a connection to the TM."""
    return Connection(paths.tm_socket())


def _taskmanager(tag=""):
    """Access Task Manager resources."""
    return TM_URL + str(tag)


# Submit tasks to the TM
def submit_tasks_tm(wf_id, tasks):
    """Submit a task to the task manager."""
    wfi = get_workflow_interface(wf_id)
    # Serialize task with json
    names = [task.name for task in tasks]
    log.info("Submitted %s to Task Manager", names)
    try:
        conn = _connect_tm()
        resp = conn.post(
            _taskmanager(),
            json=SubmitTasksRequest(tasks=tasks).model_dump(),
            timeout=5,
        )
    except requests.exceptions.ConnectionError:
        log.error("Unable to connect to task manager to submit tasks.")
        return
    # Change state of any tasks sent to the submit queue
    if resp.status_code == 200:
        for task in tasks:
            log.info("change state of %s to SUBMIT", task.name)
            wfi.set_task_state(task.id, "SUBMIT")
    else:
        log.info("Submit task to TM returned bad status: %s", resp.status_code)


def setup_workflow(wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow=None, # pylint: disable=W0613
                   tasks=None):
    """Initialize Workflow and Tasks then start workflow in separate process"""
    wfi = get_workflow_interface(wf_id)
    wfi.initialize_workflow(workflow)

    log.info("Setting workflow metadata")
    create_wf_metadata(wf_id, wf_name)
    for task in tasks:
        task.state = "" if no_start else "WAITING"
        wfi.add_task(task)

    if no_start:
        update_wf_status(wf_id, "No Start")
        log.info("Not starting workflow, as requested")
    else:
        update_wf_status(wf_id, "Starting")
        log.info("Starting workflow")
        start_workflow.delay(wf_id)


def export_dag(wf_id, output_dir, graphmls_dir, no_dag_dir, workflow_dir=None):
    """Export the DAG of the workflow."""
    wfi = get_workflow_interface(wf_id)
    wfi.export_graphml()
    dot_avail = bool(shutil.which("dot"))
    if dot_avail:
        update_graphml(wf_id, graphmls_dir)
        generate_viz(wf_id, output_dir, graphmls_dir, no_dag_dir, workflow_dir)
    else:
        update_graphml(wf_id, graphmls_dir, output_dir, no_dag_dir)
    return dot_avail


@shared_task
def start_workflow(wf_id):
    """Attempt to start the workflow, returning True if successful."""
    wfi = get_workflow_interface(wf_id)
    state = get_wf_status(wf_id)
    if state not in ("Starting", "No Start"):
        return False
    _, tasks = wfi.get_workflow()
    tasks.reverse()
    for task in tasks:
        if task.state == "":
            wfi.set_task_state(task.id, "WAITING")
    wfi.execute_workflow()
    tasks = wfi.get_ready_tasks()
    submit_tasks_tm(wf_id, tasks)
    update_wf_status(wf_id, "Running")
    return True


def copy_task_output(task):
    """Copies stdout, stderr, and metadata information to the task directory in the
        WF archive."""
    bee_workdir = get_bee_workdir()
    # Need to get this from the worker
    task_save_path = pathlib.Path(
        f"{bee_workdir}/workflows/{task.workflow_id}/{task.name}-{task.id[:4]}"
    )
    task_workdir = task.workdir
    task_metadata_path = pathlib.Path(f"{task_workdir}/{task.name}-{task.id[:4]}/"\
                f"metadata.yaml")
    if task.stdout:
        stdout_path = pathlib.Path(f"{task_workdir}/{task.stdout}")
    else:
        stdout_path = pathlib.Path(
            f"{task_workdir}/{task.name}-{task.id[:4]}/"
            f"{task.name}-{task.id[:4]}.out"
        )

    if task.stderr:
        stderr_path = pathlib.Path(f"{task_workdir}/{task.stderr}")
    else:
        stderr_path = pathlib.Path(
            f"{task_workdir}/{task.name}-{task.id[:4]}/"
            f"{task.name}-{task.id[:4]}.err"
        )

    shutil.copy(stdout_path, task_save_path / f"{task.name}-{task.id[:4]}.out")
    shutil.copy(stderr_path, task_save_path / f"{task.name}-{task.id[:4]}.err")
    shutil.copy(task_metadata_path, task_save_path / "metadata.yaml")


def flatten_metadata_dict(metadata_dict,parent_key='',sep='_',seen_keys=None):
    """Transforms a nested dictionary into a single-level dictionary for storage
        in the Neo4j database"""
    if seen_keys is None:
        seen_keys=set()
    flattened_dict = {}

    for k, v in metadata_dict.items():
        safe_key = k.replace(':', '_').replace('/', '_').replace('\\', '_')
        new_key = f"{parent_key}{sep}{safe_key}" if parent_key else safe_key

        if new_key in seen_keys:
            continue
        seen_keys.add(new_key)

        if isinstance(v, dict):
            flattened_dict.update(flatten_metadata_dict(v, new_key, sep=sep, seen_keys=seen_keys))
        elif isinstance(v, list):
            if all(isinstance(i, (str, int, float, bool, type(None))) for i in v):
                flattened_dict[new_key] = v
        elif isinstance(v, (str, int, float, bool, type(None))):
            flattened_dict[new_key] = v
    return flattened_dict

def clean_dict(metadata):
    """Removes unnecessary information from the metadata depending on
        the scheduler"""
    excluded_keys,included_keys = [],[]
    scheduler = bc.get('DEFAULT','workload_scheduler').lower()
    if scheduler == 'slurm' and bc.get('slurm','use_commands'):
        excluded_keys =[
        "GroupId", "MCS_label", "Nice", "Dependency", "Requeue", "Restarts",
        "BatchFlag", "Reboot", "TimeMin", "Deadline", "SuspendTime", "SecsPreSuspend",
        "LastSchedEval", "Scheduler", "ReqNodeList", "ExcNodeList", "ReqTRES",
        "AllocTRES", "Socks/Node", "CoreSpec", "MinCPUsNode", "MinMemoryNode",
        "MinTmpDiskNode", "Features", "DelayBoot", "OverSubscribe", "Contiguous",
        "Licenses", "Network","BatchHost", "NtasksPerN_B_S_C", "ReqB_S_C_T", "Socks_Node",
        "WorkDir", "duration", "job_name","start_time","AllocNode_Sid","Priority"]

    elif scheduler == 'flux':
        excluded_keys =["exception","uri","annotations","success","bank","project",
        "duration","t_depend","t_cleanup","cwd","urgency","dependencies","state",
        "ranks","annotations_user_uri","exception_note","exception_occurred",
        "exception_severity","exception_type","expiration","priority","result"]
    else:
        included_keys = ["account","accrue_time_number","allocating_node","cluster",
        "command","eligible_time_number","end_time_number","exit_code_status",
        "exit_code_return_code_number","failed_node","job_id","job_resources",
        "job_state","last_sched_evaluation_number","licenses_allocated",
        "name","nodes","partition","priority_by_partition","qos","scheduled_nodes",
        "step_id_sluid","step_id_job_id_number","start_time_number","standard_input",
        "standard_output","standard_error","stdin_expanded","stdout_expanded",
        "stderr_expanded","submit_time_number","submit_line","suspend_time_number",
        "tres_alloc_str"]

    for k in list(metadata):
        if scheduler == 'slurm' and not bc.get('slurm','use_commands'):
            if k not in included_keys or k.startswith(("_","--")):
                metadata.pop(k,None)
        else:
            if k in excluded_keys or k.startswith(("_","--")):
                metadata.pop(k,None)

    match_metadata = helper_clean_dict(metadata,scheduler)
    cleaned_metadata = standardize_time(match_metadata,scheduler)
    return cleaned_metadata

def helper_clean_dict(metadata,scheduler):
    """Ensures the attributes in the config match with what the schedulers return"""
    if scheduler == 'slurm' and not bc.get('slurm','use_commands'):
        for k in list(metadata):
            if k.endswith("_number"):
                new_key = k.removesuffix("_number")
                if new_key == "exit_code_return_code":
                    new_key = "exit_code_number"
                metadata[new_key] = metadata.pop(k)
    return metadata

def standardize_time(metadata,scheduler):
    """Standardize the time attributes across the schedulers"""
    if scheduler == 'slurm' and not bc.get('slurm','use_commands'):
        time = {"end_time","start_time","submit_time","suspend_time","eligible_time",
                "accrue_time","last_sched_evaluation"}
        for k in list(metadata):
            if k in time:
                if metadata[k] == 0:
                    metadata[k] = 0
                else:
                    metadata[k] = dt.fromtimestamp(metadata[k]).strftime('%Y-%m-%d %H:%M:%S')
    elif scheduler == 'slurm' and bc.get('slurm','use_commands'):
        time = {"AccrueTime","EligibleTime","EndTime","SubmitTime","StartTime"}
        for k in list(metadata):
            if k in time:
                if metadata[k] == 0 or metadata[k] == 'Unknown':
                    metadata[k] = 0
                else:
                    metadata[k] = dt.fromisoformat(metadata[k]).strftime('%Y-%m-%d %H:%M:%S')
    return metadata
  