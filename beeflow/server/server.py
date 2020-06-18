"""Server launch script."""

import os
import sys
import platform
import jsonpickle
import requests
import cwl_utils.parser_v1_0 as cwl
# Server and REST handlin
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse
# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage
import beeflow.common.parser.parse_cwl as parser
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.config.config_driver import BeeConfig

try:
    bc = BeeConfig(userconfig=sys.argv[1])
except IndexError:
    bc = BeeConfig()

# Set Workflow manager ports, attempt to prevent collisions
WM_PORT = 5000

if platform.system() == 'Windows':
    # Get parent's pid to offset ports. uid method better but not available in Windows
    WM_PORT += os.getppid() % 100
else:
    WM_PORT += os.getuid() % 100

if bc.userconfig.has_section('workflow_manager'):
    # Try getting listen port from config if exists, use WM_PORT if it doesnt exist
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port', WM_PORT)
else:
    print("[workflow_manager] section not found in configuration file, default values\
 will be added")

    wfm_dict = {
        'listen_port': WM_PORT,
    }

    bc.modify_section('user', 'workflow_manager', wfm_dict)

    sys.exit("Please check " + str(bc.userconfig_file) + " and restart WorkflowManager")

if bc.userconfig.has_section('task_manager'):
    # Try getting listen port from config if exists, use 5050 if it doesnt exist
    TM_LISTEN_PORT = bc.userconfig['task_manager'].get('listen_port', '5050')
else:
    print("[task_manager] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    TM_LISTEN_PORT = 5050
    if platform.system() == 'Windows':
        # Get parent's pid to offset ports. uid method better but not available in Windows
        TM_LISTEN_PORT += os.getppid() % 100
    else:
        TM_LISTEN_PORT += os.getuid() % 100

flask_app = Flask(__name__)
api = Api(flask_app)

UPLOAD_FOLDER = 'workflows'
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Returns the url to the TM
def _url():
    task_manager = "/bee_tm/v1/task/"
    return f'http://127.0.0.1:{TM_LISTEN_PORT}/{task_manager}'


# Used to access the TM
def _resource(tag=""):
    return _url() + str(tag)


# Instantiate the workflow interface
try:
    wfi = WorkflowInterface(userconfig=sys.argv[1])
except IndexError:
    wfi = WorkflowInterface()


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

    # Give client a wf_id
    # wf_id not needed if we just support a single workflow
    def post(self):
        """TEMPORARY: Hard-coded lister to get workflow 42."""
        data = self.reqparse.parse_args()
        title = data['title']
        print("Retrieved a title \"{}\". What to do with it?".format(title))
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
    def put(self, wf_id):
        """Get a workflow or give file not found error."""
        print("JobSubmit passed wf_id={} but it's unused. What do?".format(wf_id))
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
            parser.create_workflow(top, wfi)
            resp = make_response(jsonify(msg='Workflow uploaded', status='ok'), 201)
            return resp
        resp = make_response(jsonify(msg='File corrupted', status='error'), 400)
        return resp


# Submit a task to the TM
def submit_task(task):
    """Submit a task to the task manager."""
    # Serialize task with json
    task_json = jsonpickle.encode(task)
    # Send task_msg to task manager
    print(f"Submitted {task.name} to Task Manager")
    resp = requests.post(_resource("submit/"), json={'task': task_json})
    if resp.status_code != 200:
        print("Something bad happened")


# Used to tell if the workflow is currently paused
# Will eventually be moved to a Workflow class
WORKFLOW_PAUSED = False
SAVED_TASK = None


# Save a task when we pause
def save_task(task):
    """Save a task."""
    global SAVED_TASK
    print(f"Saving {task.name}")
    SAVED_TASK = task


def resume():
    """Resume a saved task."""
    global SAVED_TASK
    if SAVED_TASK is not None:
        submit_task(SAVED_TASK)
    # Clear out the saved task
    SAVED_TASK = None


# This class is where we act on existing jobs
class JobActions(Resource):
    """Class to handle job actions."""

    def __init__(self):
        """Initialize JobActions class with passed json object."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    def post(self, wf_id):
        """Start job. Send tasks to the task manager."""
        print("JobActions took wf_id={} as argument but it was unused.".format(wf_id))
        print("self is referenced but not used. Evaluate JobActions().post decorators", self)
        # Get first task and send it to the task manager
        task = list(wfi.get_dependent_tasks(wfi.get_task_by_id(0)))[0]
        # Submit task to TM
        submit_task(task)
        return "Started workflow!"

    def get(self, wf_id):
        """Check the database for the current status of all the tasks."""
        print("JobActions took wf_id={} as argument but it was unused.".format(wf_id))
        print("self is referenced but not used. Evaluate JobActions().get decorators", self)
        (tasks, requirements, hints) = wfi.get_workflow()
        print('requirements={} obtained but unused. Either use or change argument to _'.
              format(requirements))
        print('hints={} obtained but unused. Either use or change argument to _'.
              format(hints))
        task_status = ""
        for task in tasks:
            if task.name != "bee_init" and task.name != "bee_exit":
                task_status += f"{task.name}--{wfi.get_task_state(task)}\n"
        print("Returned query")
        resp = make_response(jsonify(msg=task_status, status='ok'), 200)
        return resp

    def delete(self, wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        print("JobActions took wf_id={} as argument but it was unused.".format(wf_id))
        print("self is referenced but not used. Evaluate JobActions().get decorators", self)
        resp = requests.delete(_resource())
        if resp.status_code != 200:
            print("Something bad happened")
        # Remove all tasks currently in the database
        wfi.finalize_workflow()
        # wfi.cleanup()
        print("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        print("JobActions took wf_id={} as argument but it was unused.".format(wf_id))
        global WORKFLOW_PAUSED
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        if option == 'pause':
            WORKFLOW_PAUSED = True
            print("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
            return resp
        if option == 'resume':
            if WORKFLOW_PAUSED:
                WORKFLOW_PAUSED = False
                resume()
            print("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        print("Invalid option")
        resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
        return resp


class JobUpdate(Resource):
    """Class for to interact with an existing job."""

    def __init__(self):
        """Initialize JobUpdate with task_id and job_state requirements."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task_id', type=int, location='json',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='json',
                                   required=True)

    def put(self):
        """Update the state of a task from the task manager."""
        # Figure out how to find the task in the databse and change it's state
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']
        print(f"Task_id: {task_id} State {job_state}")

        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)

        if job_state == "COMPLETED":
            remaining_tasks = list(wfi.get_dependent_tasks(wfi.get_task_by_id(task_id)))
            if len(remaining_tasks) == 0:
                print("Workflow Completed")
                wfi.finalize_workflow()
                print("Cleanup")
                # wfi.cleanup()

            task = remaining_tasks[0]
            if task.name != 'bee_exit':
                # Take the first task and schedule it
                # TODO This won't work well for deeply nested workflows
                if WORKFLOW_PAUSED:
                    # If we've paused the workflow save the task until we resume
                    save_task(task)
                else:
                    submit_task(task)
            else:
                print("Workflow Completed!")
                wfi.finalize_workflow()
                # wfi.cleanup()
        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp


api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<string:wf_id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')


if __name__ == '__main__':
    flask_app.run(debug=True, port=str(wfm_listen_port))

# pylama:ignore=W0511
