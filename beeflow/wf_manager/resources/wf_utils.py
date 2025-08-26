"""Utility functions for wf_manager resources."""

import os
import shutil
import pathlib
import requests
import jsonpickle
from celery import shared_task # pylint: disable=W0611 # pylint can't find celery imports

from beeflow.common import log as bee_logging
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.gdb import neo4j_driver
from beeflow.common.gdb.generate_graph import generate_viz
from beeflow.common.gdb.graphml_key_updater import update_graphml
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.connection import Connection
from beeflow.common import paths
from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db
from beeflow.common.deps.neo4j_manager import connect_neo4j_driver


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
        return TM_URL + str(tag)
    if component == "sched":
        return SCHED_URL + str(tag)

    raise ValueError(f"Invalid component: {component}")


# Submit tasks to the TM
def submit_tasks_tm(wf_id, tasks, allocation): # pylint: disable=W0613
    """Submit a task to the task manager."""
    wfi = get_workflow_interface(wf_id)
    for task in tasks:
        metadata = wfi.get_task_metadata(task)
        task.workdir = metadata['workdir']
    # Serialize task with json
    tasks_json = jsonpickle.encode(tasks)
    # Send task_msg to task manager
    names = [task.name for task in tasks]
    log.info("Submitted %s to Task Manager",names)
    try:
        conn = _connect_tm()
        resp = conn.post(_resource('tm', "submit/"), json={'tasks': tasks_json},
                         timeout=5)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to task manager to submit tasks.')
        return
    # Change state of any tasks sent to the submit queue
    if resp.status_code == 200:
        for task in tasks:
            log.info("change state of %s to SUBMIT",task.name)
            wfi.set_task_state(task, 'SUBMIT')
    else:
        log.info("Submit task to TM returned bad status: %s",resp.status_code)


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
        log.info("Something bad happened %s",resp.status_code)
        return "Did not work"
    return resp.json()


def schedule_submit_tasks(wf_id, tasks):
    """Schedule and then submit tasks to the TM."""
    # Submit ready tasks to the scheduler
    allocation = submit_tasks_scheduler(tasks)
    # Submit tasks to TM
    submit_tasks_tm(wf_id, tasks, allocation)


def setup_workflow(wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow=None, # pylint: disable=W0613
                   tasks=None):
    """Initialize Workflow in Separate Process."""
    wfi = get_workflow_interface(wf_id)
    wfi.initialize_workflow(workflow)

    log.info('Setting workflow metadata')
    create_wf_metadata(wf_id, wf_name)
    db = connect_db(wfm_db, get_db_path())
    for task in tasks:
        task_state = "" if no_start else "WAITING"
        wfi.add_task(task, task_state)
        metadata = wfi.get_task_metadata(task)
        if metadata.get('workdir') is None:
            metadata['workdir'] = task.workdir
            wfi.set_task_metadata(task, metadata)
        db.workflows.add_task(task.id, wf_id, task.name, task_state)

    if no_start:
        update_wf_status(wf_id, 'No Start')
        db.workflows.update_workflow_state(wf_id, 'No Start')
        log.info('Not starting workflow, as requested')
    else:
        update_wf_status(wf_id, 'Waiting')
        db.workflows.update_workflow_state(wf_id, 'Waiting')
        log.info('Starting workflow')
        db.workflows.update_workflow_state(wf_id, 'Running')
        start_workflow(wf_id)


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


def start_workflow(wf_id):
    """Attempt to start the workflow, returning True if successful."""
    db = connect_db(wfm_db, get_db_path())
    wfi = get_workflow_interface(wf_id)
    state = wfi.get_workflow_state()
    if state in ('RUNNING', 'PAUSED', 'COMPLETED'):
        return False
    _, tasks = wfi.get_workflow()
    tasks.reverse()
    for task in tasks:
        task_state = wfi.get_task_state(task)
        if task_state == '':
            wfi.set_task_state(task, 'WAITING')
            db.workflows.update_task_state(task.id, wf_id, 'WAITING')
    wfi.execute_workflow()
    tasks = wfi.get_ready_tasks()
    schedule_submit_tasks(wf_id, tasks)
    wf_id = wfi.workflow_id
    update_wf_status(wf_id, 'Running')
    db.workflows.update_workflow_state(wf_id, 'Running')
    return True


def copy_task_output(task, wfi):
    """Copies stdout, stderr, and metadata information to the task directory in the
        WF archive."""
    bee_workdir = get_bee_workdir()
    # Need to get this from the worker
    task_save_path = pathlib.Path(
            f"{bee_workdir}/workflows/{task.workflow_id}/{task.name}-{task.id[:4]}"
    )
    task_workdir = wfi.get_task_metadata(task)["workdir"]

    task_metadata_path = pathlib.Path(f"{task_workdir}/{task.name}-{task.id[:4]}/"\
                f"metadata.txt")

    if task.stdout:
        stdout_path = pathlib.Path(f"{task_workdir}/{task.stdout}")
    else:
        stdout_path = pathlib.Path(f"{task_workdir}/{task.name}-{task.id[:4]}/"\
                f"{task.name}-{task.id[:4]}.out")

    if task.stderr:
        stderr_path = pathlib.Path(f"{task_workdir}/{task.stderr}")
    else:
        stderr_path = pathlib.Path(f"{task_workdir}/{task.name}-{task.id[:4]}/"\
                f"{task.name}-{task.id[:4]}.err")

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
