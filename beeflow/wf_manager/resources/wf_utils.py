"""Utility functions for wf_manager resources."""

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


def _resource(tag=""):
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
            _resource(),
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


def schedule_submit_tasks(wf_id, tasks):
    """Submit ready tasks directly to the TM."""
    submit_tasks_tm(wf_id, tasks)


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
    schedule_submit_tasks(wf_id, tasks)
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
                f"metadata.txt")
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
    shutil.copy(task_metadata_path, task_save_path / "metadata.txt")


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

def clean_dict(metadata_dict):
    """Removes unnecessary information from the metadata depending on
        the scheduler"""
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
        excluded_keys = [
        "billable_tres", "minimum_switches", "exclusive", "system_comment", "het_job_id",
        "group_name","profile", "tres_per_job", "tasks_per_board_number", 
        "max_cpus_infinite", "selinux_context","tasks_per_socket_set", "container_id",
        "sockets_per_node_set", "user_name", "delay_boot_number","admin_comment",
        "time_minimum_infinite", "tasks_per_tres_infinite", "cluster_features",
        "deadline", "minimum_tmp_disk_per_node_infinite", "minimum_cpus_per_node_infinite",
        "licenses","max_cpus_set", "cpu_frequency_minimum_infinite", 
        "job_resources_allocated_cpus","tasks_per_node_number", "cores_per_socket_infinite",
        "threads_per_core_set","job_resources_allocated_hosts", "hold",
        "cpu_frequency_maximum_number", "features","time_minimum_number", "tasks_per_core_set",
        "show_flags", "tasks_infinite","cpu_frequency_governor_infinite", "tres_req_str",
        "tasks_per_board_set", "cron", "oversubscribe","node_count_set", "memory_per_cpu_number",
        "wckey", "exit_code_set", "tasks_per_core_number","batch_flag",
        "threads_per_core_infinite", "time_limit_set", "array_job_id_infinite","contiguous",
        "federation_siblings_viable", "batch_features", "restart_cnt","memory_per_node_set",
        "array_job_id_number", "minimum_cpus_per_node_number","array_task_id_set",
        "threads_per_core_number", "cpus_per_task_set", "delay_boot_set","time_limit_infinite",
        "pre_sus_time", "tasks_per_board_infinite", "tres_freq","het_job_id_number",
        "tres_per_task", "het_job_offset_number", "priority_number", "mail_user",
        "tasks_per_tres_number", "comment", "array_task_id_infinite",
        "minimum_tmp_disk_per_node_number","memory_per_tres", "resize_time", "cpus_set",
        "cores_per_socket_set", "preemptable_time","cpus_per_tres", "federation_siblings_active",
        "cpu_frequency_maximum_infinite","tasks_per_socket_infinite", "memory_per_node_infinite",
        "tasks_per_tres_set","sockets_per_node_number", "maximum_switch_wait_time", "power_flags",
        "mcs_label", "core_spec","tres_bind", "required_nodes", "user_id", "federation_origin",
        "memory_per_cpu_set","time_limit_number", "flags", "job_resources_allocated_cores",
        "billable_tres_infinite","delay_boot_infinite", "max_nodes_number", "mail_type",
        "tasks_per_socket_number","sockets_per_board", "array_max_tasks_set", "array_job_id_set",
        "tasks_per_node_set", "nice","cpu_frequency_minimum_number", "last_sched_evaluation",
        "het_job_offset_infinite","tres_per_node", "burst_buffer", "excluded_nodes",
        "time_minimum_set","cpus_per_task_infinite","prefer", "derived_exit_code_set",
        "cpu_frequency_minimum_set","job_size_str", "priority_set","state_description",
        "het_job_id_set", "cpus_infinite","burst_buffer_state", "tres_per_socket",
        "array_task_string", "max_nodes_infinite","cpu_frequency_governor_set",
        "cores_per_socket_number", "exit_code_infinite","minimum_cpus_per_node_set","preempt_time",
        "derived_exit_code_infinite","cpu_frequency_governor_number", "thread_spec", "gres_detail",
        "memory_per_node_number","cpus_per_task_number","network", "array_max_tasks_number",
        "resv_name", "cpu_frequency_maximum_set","extra","het_job_id_infinite","state_reason",
        "node_count_number","max_nodes_set", "het_job_offset_set","reboot", 
        "minimum_tmp_disk_per_node_set", "tasks_set","max_cpus_number", "cpus_number", "group_id",
        "tasks_per_core_infinite", "suspend_time", "array_max_tasks_infinite", "association_id",
        "job_resources_nodes","container","dependency","requeue", "node_count_infinite",
        "memory_per_cpu_infinite","batch_host", "array_task_id_number","tasks_number",
        "billable_tres_set","tasks_per_node_infinite","sockets_per_node_infinite",
        "priority_infinite","array_job_id","shared","derived_exit_code_number",
        "billable_tres_number","current_working_directory"]

    for k in list(metadata_dict):
        if k in excluded_keys:
            metadata_dict.pop(k,None)
    return metadata_dict
