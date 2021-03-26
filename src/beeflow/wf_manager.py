"""Server launch script."""
import os
import sys
import logging
import configparser
import jsonpickle
import requests
import random
import time
import types
import cwl_utils.parser_v1_0 as cwl
# Server and REST handlin
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse
# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage
# Temporary clamr parser
import beeflow.common.parser.parse_clamr as parser
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging
import beeflow.common.wf_profiler as wf_profiler

if len(sys.argv) > 2:
    bc = BeeConfig(userconfig=sys.argv[1])
else:
    bc = BeeConfig()

if bc.userconfig.has_section('workflow_manager'):
    # Try getting listen port from config if exists, use WM_PORT if it doesnt exist
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port)
    log.info(f"wfm_listen_port {wfm_listen_port}")
else:
    log.info("[workflow_manager] section not found in configuration file, default values\
 will be added")

    wfm_dict = {
        'listen_port': bc.default_wfm_port,
    }

    bc.modify_section('user', 'workflow_manager', wfm_dict)
    sys.exit("Please check " + str(bc.userconfig_file) + " and restart WorkflowManager")

if bc.userconfig.has_section('task_manager'):
    # Try getting listen port from config if exists, use default if it doesnt exist
    TM_LISTEN_PORT = bc.userconfig['task_manager'].get('listen_port', bc.default_tm_port)
else:
    log.info("[task_manager] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    TM_LISTEN_PORT = bc.default_tm_port

if bc.userconfig.has_section('scheduler'):
    # Try getting listen port from config if exists, use 5050 if it doesnt exist
    SCHED_LISTEN_PORT = bc.userconfig['scheduler'].get('listen_port', bc.default_sched_port)
else:
    log.info("[scheduler] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    SCHED_LISTEN_PORT = bc.default_sched_port

flask_app = Flask(__name__)
api = Api(flask_app)

UPLOAD_FOLDER = 'workflows'
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def tm_url(host, port):
    """Get Task Manager url."""
    task_manager = "bee_tm/v1/task/"
    if host is None or port is None:
        return f'http://127.0.0.1:{TM_LISTEN_PORT}/{task_manager}'
    return f'http://{host}:{port}/{task_manager}'


def sched_url():
    """Get Scheduler url."""
    scheduler = "bee_sched/v1/"
    return f'http://127.0.0.1:{SCHED_LISTEN_PORT}/{scheduler}'


def _resource(component, tag="", host=None, port=None):
    """Access Task Manager or Scheduler."""
    if component == "tm":
        url = tm_url(host, port) + str(tag)
    elif component == "sched":
        url = sched_url() + str(tag)
    return url


# Instantiate the workflow interface
try:
    wfi = WorkflowInterface(user='neo4j', bolt_port=bc.userconfig.get('graphdb', 'bolt_port'),
                            db_hostname=bc.userconfig.get('graphdb', 'hostname'),
                            password=bc.userconfig.get('graphdb', 'dbpass'))

except KeyError:
    wfi = WorkflowInterface()


class ResourceMonitor():
    """Class def to interact with resource monitor."""

    def __init__(self):
        """Construct resource monitor."""
        #self.hostname = os.uname()[1].split('.')[0]
        #self.nodes = 32
        self.resources = {}

    def get(self):
        """Construct data dictionary for resource monitor."""
        #data = {
        #        'hostname': self.hostname,
        #        'nodes': self.nodes
        #        }

        #return data
        return {id_: self.resources[id_] for id_ in self.resources}

    def add(self, id_, resource):
        """Add a resource to the system."""
        self.resources[id_] = resource


rm = ResourceMonitor()


def validate_wf_id(func):
    """Validate tempoary hard coded workflow id."""
    def wrapper(*args, **kwargs):
        wf_id = int(kwargs['wf_id'])
        if wf_id != 42:
            log.info(f'Wrong workflow id. Set to {wf_id}, but should be 42')
            resp = make_response(jsonify(status='wf_id not found'), 404)
            return resp
        return func(*args, **kwargs)
    return wrapper


# Client registers with the workflow manager.
# Workflow manager returns a workflow ID used for subsequent communication
class JobsList(Resource):
    """Class def to interact with workflow job listing."""

    def __init__(self):
        """Initialize job list class."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                   help='Need a title',
                                   location='json')
        super(JobsList, self).__init__()

    def post(self):
        """Give client a workflow id."""
        # wf_id not needed if we just support a single workflow
        data = self.reqparse.parse_args()
        # title = data['title'] Not currently needed.
        # Will probably be incorporated with a GUI client down the road

        # Return the wf_id and created
        resp = make_response(jsonify(wf_id="42"), 201)
        return resp


# User submits the actual workflow.
class JobSubmit(Resource):
    """Class to submit jobs to workflow manager."""

    def __init__(self):
        """Initialize workflow manager from parsed arguments."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage,
                                   location='files', required=True)

    # Client Submits workflow
    @validate_wf_id
    def put(self, wf_id):
        # wf_id requires support in the GDB which we do not currently have
        # Ignore pylama error with noqa
        """Get a workflow or give file not found error."""
        data = self.reqparse.parse_args()
        if data['workflow'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp

        # Workflow file
        cwl_file = data['workflow']
        if cwl_file:
            # TODO get the filename
            cwl_file.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], "work.cwl"))
            # Parse the workflow and add it to the database
            # This is just work.cwl until I can find a way to ensure persistent data
            top = cwl.load_document("./workflows/work.cwl")
            if wfi.workflow_initialized() and wfi.workflow_loaded():
                # Clear the workflow if we've already run one
                # TODO Export the workflow here
                wfi.finalize_workflow()

            parser.create_workflow(top, wfi)
            resp = make_response(jsonify(msg='Workflow uploaded', status='ok'), 201)
            return resp
        resp = make_response(jsonify(msg='File corrupted', status='error'), 400)
        return resp


# Submit a task to the TM
def submit_task_tm(alloc, task):
    """Submit a task to the task manager."""
    task_allocations[task.id] = alloc
    # Serialize task with json
    task_json = jsonpickle.encode(task)
    # host, port, resources = choose_tm(task.id)
    # log.info("Running %s on %s:%i" % (task.name, host, port))
    # Send task_msg to task manager
    log.info(f"Submitted {task.name} to Task Manager")
    # Get the Task Manager information
    assert len(alloc) > 0
    # Choose the first allocation for now
    host, port = alloc[0]['id_'].split(':')
    log.info(f'Submitting to TM {host}:{port}')
    # TODO: This ignores all allocation details except the resource itself
    port = int(port)
    resp = requests.post(_resource('tm', "submit/", host=host, port=port),
                         json={'task': task_json})
    if resp.status_code != 200:
        log.info(f"Submit task to TM returned bad status: {resp.status_code}")


# dict of task_id -> allocation info (if the task is running)
# TODO: this should perhaps be put in the database
task_allocations = {}


# Submit a list of tasks to the Scheduler
def submit_tasks_scheduler(sched_tasks):
    """Submit a list of tasks to the scheduler."""
    tasks_json = jsonpickle.encode(sched_tasks)
    log.info(f"Submitted {sched_tasks} to Scheduler")
    # The workflow name will eventually be added to the wfi workflow object
    log.info(_resource('sched', "workflows/workflow/jobs"))
    resp = requests.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks)
    if resp.status_code != 200:
        log.info(f"Something bad happened {resp.status_code}")
    allocation = resp.json()
    return {alloc['task_name']: alloc['allocations'] for alloc in allocation}


def setup_scheduler():
    """Get info from the resource monitor and sends it to the scheduler."""
    # Get the info for the current server
    nodes = 32

    data = rm.get()
    log.info(data)

    resources = [{'id_': id_, 'nodes': data[id_]['nodes']} for id_ in data]
    log.info(resources)

    log.info(_resource('sched', "resources/"))
    #resp = requests.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks)
    try:
        # setup_scheduler()
        resp = requests.put(_resource('sched', "resources"), json=resources)
        log.info(resp.json())
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to scheduler')


# Used to tell if the workflow is currently paused
# Will eventually be moved to a Workflow class
WORKFLOW_PAUSED = False
SAVED_TASK = None


# Save a task when we pause
def save_task(task):
    """Save a task."""
    global SAVED_TASK
    log.info(f"Saving {task.name}")
    SAVED_TASK = task


def resume():
    """Resume a saved task."""
    global SAVED_TASK
    if SAVED_TASK is not None:
        # TODO: Need to keep track of allocations (perhaps in the database)
        submit_task_tm(alloc, SAVED_TASK)
    # Clear out the saved task
    SAVED_TASK = None


def tasks_to_sched(tasks):
    """Convert gdb tasks to sched tasks."""
    sched_tasks = []
    for task in tasks:
        sched_task = {
            'workflow_name': 'workflow',
            'task_name': task.id,
            'requirements': {
                'max_runtime': 1,
                'nodes': 1
            }
        }
        sched_tasks.append(sched_task)
    return sched_tasks


# TODO: Change the name to the real name of the workflow
profiler = wf_profiler.WorkflowProfiler('test_workflow')


# This class is where we act on existing jobs
class JobActions(Resource):
    """Class to handle job actions."""

    def __init__(self):
        """Initialize JobActions class with passed json object."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    @staticmethod
    @validate_wf_id
    def post(wf_id):
        """Start job. Send tasks to the task manager."""
        # Begin execution
        wfi.execute_workflow()

        # Get dependent tasks that branch off of bee_init and send to the scheduler
        # tasks = list(wfi.get_dependent_tasks(wfi.get_task_by_id(0)))
        tasks = list(wfi.get_ready_tasks())
        # Convert to a scheduler task object
        sched_tasks = tasks_to_sched(tasks)
        # Submit all dependent tasks to the scheduler
        allocation = submit_tasks_scheduler(sched_tasks)
        profiler.add_scheduling_results(rm.resources, allocation)
        log.info(f"Scheduler says {allocation}")
        # Submit tasks to TM
        for task in tasks:
            alloc = allocation[task.id]
            # log.info('task alloc', alloc)
            submit_task_tm(alloc, task)
        # submit_task_tm(tasks[0])
        #resp = make_response(jsonify(msg='Started workflow', status='ok'), 200)
        return "Started Workflow"

    @staticmethod
    @validate_wf_id
    def get(wf_id):
        """Check the database for the current status of all the tasks."""
        (tasks, _, _) = wfi.get_workflow()
        task_status = ""
        for task in tasks:
            if task.name != "bee_init" and task.name != "bee_exit":
                task_status += f"{task.name}--{wfi.get_task_state(task)}\n"
        log.info("Returned query")
        resp = make_response(jsonify(msg=task_status, status='ok'), 200)
        return resp

    @staticmethod
    @validate_wf_id
    def delete(wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        resp = requests.delete(_resource('tm'))
        if resp.status_code != 200:
            log.info(f"Delete from task manager returned bad status: {resp.status_code}")
        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    @validate_wf_id
    def patch(self, wf_id):
        """Pause or resume workflow."""
        global WORKFLOW_PAUSED
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        if option == 'pause':
            WORKFLOW_PAUSED = True
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
            return resp
        if option == 'resume':
            if WORKFLOW_PAUSED:
                WORKFLOW_PAUSED = False
                resume()
            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        log.error("Invalid option")
        resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
        return resp


class JobUpdate(Resource):
    """Class to interact with an existing job."""

    def __init__(self):
        """Initialize JobUpdate with task_id and job_state requirements."""
        self.reqparse = reqparse.RequestParser()
        #self.reqparse.add_argument('task_id', type=int, location='json',
        #                           required=True)
        self.reqparse.add_argument('task_id', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='json',
                                   required=True)

    def put(self):
        """Update the state of a task from the task manager."""
        # Figure out how to find the task in the databse and change it's state
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']

        task = wfi.get_task_by_id(task_id)

        # Save profiling data
        profiler.add_state_change(task, job_state)

        wfi.set_task_state(task, job_state)
        wfi.initialize_ready_tasks()
        # assert wfi.get_task_state(task) == job_state

        remaining_tasks = list(wfi.get_ready_tasks())
        # if job_state == "COMPLETED":
        if remaining_tasks and job_state == "COMPLETED":
            # remaining_tasks = list(wfi.get_dependent_tasks(wfi.get_task_by_id(task_id)))

            tasks = remaining_tasks
            # TODO: Stop using bee_exit
            # if remaining_tasks[0].name != 'bee_exit':
            # Take the first task and schedule it
            # TODO This won't work well for deeply nested workflows
            if WORKFLOW_PAUSED:
                # If we've paused the workflow save the task until we resume
                save_task(task)
            else:
                sched_tasks = tasks_to_sched(remaining_tasks)
                if len(remaining_tasks) == 0:
                    log.info("Workflow Completed")
                else:
                    allocation = submit_tasks_scheduler(sched_tasks)
                    profiler.add_scheduling_results(rm.resources, allocation)
                    metadata = wfi.get_task_metadata(tasks[0], ['allocation'])
                    # Set allocation information
                    # TODO: Perhaps this should go in the database, but I'm not sure
                    # metadata['allocation'] = allocation
                    # wfi.set_task_metadata(tasks[0], metadata)
                    for task in tasks:
                        # submit_task_tm(allocation[tasks[0].id], tasks[0])
                        # TODO: Other profiling here
                        submit_task_tm(allocation[task.id], task)
        # TODO: Call wfi.workflow_completed()?
        elif wfi.workflow_completed():
            # Save profiling data
            profiler.save()
            log.info("Workflow Completed!")
        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp


# Global Task Manager information
task_managers = {}
queue = []
tasks_to_tm = {}


def choose_tm(task_id):
    """Choose the task manager to launch the given task on."""
    tms = list(task_managers)
    # TODO: Need to invoke the scheduler to determine which Task Manager to run
    # it on. This should also take into account if a given TM seems to not be
    # running right now.
    # Just randomly choose a task manager right now
    host, port = tms[random.randint(0, len(tms) - 1)]
    # Get the status and resource information from the Task Manager
    # TODO: Use the resource information to do scheduling
    resp = requests.get('http://%s:%i/bee_tm/v1/status/' % (host, port))
    resp_data = resp.json()
    resources = resp_data['resources']
    tasks_to_tm[task_id] = (host, port)
    return host, port, resources


class TM(Resource):
    """Class to interact with the Task Managers."""

    def __init__(self):
        """Initialize the requirements for Task Manager data."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tm_listen_host', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('tm_listen_port', type=int, location='json',
                                   required=True)
        self.reqparse.add_argument('resource', type=dict, location='json',
                                   required=True)

    def post(self):
        """Add Task Manager information to the WFM Task Manager data."""
        log.info('POST TM')
        data = self.reqparse.parse_args()
        res = data['resource']
        host, port = data['tm_listen_host'], data['tm_listen_port']
        log.info('Updating TM at %s:%i' % (host, port))
        key = (host, port)
        # Add the Task Manager to the list of task managers
        task_managers[key] = {
            'last_message_time': int(time.time()),
        }
        log.info('Adding resource information')
        rm.add('%s:%i' % (host, port), res)

        # TODO: Add scheduler input information + resources
        setup_scheduler()
        # TODO: Need to update the scheduler
        # TODO: Perhaps send information to the resource manager
        return make_response(jsonify(status='Created'), 201)


api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<string:wf_id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')
api.add_resource(TM, '/bee_wfm/v1/task_managers/')


if __name__ == '__main__':
    # Setup the Scheduler
    # setup_scheduler()

    log.info(f'wfm_listen_port:{wfm_listen_port}')

    bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    # Putting this off for another issue so noqa to appease the lama
    flask_app.logger.addHandler(handler) #noqa
    flask_app.run(debug=True, port=str(wfm_listen_port))

# pylama:ignore=W0511
