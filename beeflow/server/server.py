#!flask/bin/python3
import os
import sys
import jsonpickle
import requests
import random
import cwl_utils.parser_v1_0 as cwl
import beeflow.common.parser.parse_cwl as parser
import platform

# Server and REST handling
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage

from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.config.config_driver import BeeConfig

try:
    bc = BeeConfig(userconfig=sys.argv[1])
except IndexError:
    bc = BeeConfig()

# Set Workflow manager ports, attempt to prevent collisions
wm_port=5000
if platform.system() == 'Windows':
    # Get parent's pid to offset ports. uid method better but not available in Windows
    wm_port += os.getppid()%100
else:
    wm_port += os.getuid()%100

if bc.userconfig.has_section('workflow_manager'):
    # Try getting listen port from config if exists, use wm_port if it doesnt exist
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',wm_port)
else:
    print("[workflow_manager] section not found in configuration file, default values will be added")

    wfm_dict = {
        'listen_port': wm_port,
    }

    bc.add_section('user', 'workflow_manager', wfm_dict)

    sys.exit("Please check " + str(bc.userconfig_file) + " and restart WorkflowManager")

if bc.userconfig.has_section('task_manager'):
    # Try getting listen port from config if exists, use 5050 if it doesnt exist
    tm_listen_port = bc.userconfig['task_manager'].get('listen_port','5050')
else:
    print("[task_manager] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    tm_listen_port=5050
    if platform.system() == 'Windows':
        # Get parent's pid to offset ports. uid method better but not available in Windows
        tm_listen_port += os.getppid()%100
    else:
        tm_listen_port += os.getuid()%100

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
    return f'http://127.0.0.1:{tm_listen_port}/{task_manager}'

# Used to access the TM
def _resource(tag=""): 
    return _url() + str(tag)

# Instantiate the workflow interface
wfi = WorkflowInterface()

# Client registers with the workflow manager.
# Workflow manager returns a workflow ID used for subsequent communication
class JobsList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                    help='Need a title',
                                    location='json')
        super(JobsList, self).__init__()

    # Give client a wf_id
    # wf_id not needed if we just support a single workflow
    def post(self):
        data = self.reqparse.parse_args()
        title = data['title']
        # Return the wf_id and created
        resp = make_response(jsonify(wf_id="42"), 201)
        return resp

# User submits the actual workflow. 
class JobSubmit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, 
             location='files', required=True)

    # Client Submits workflow 
    def put(self, wf_id):
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
        else:
            resp = make_response(jsonify(msg='File corrupted', status='error'), 400)
            return resp

# Submit a task to the TM
def submit_task(task):
    # Serialize task with json
    task_json = jsonpickle.encode(task)
    # Send task_msg to task manager
    print(f"Submitted {task.name} to Task Manager")
    resp = requests.post(_resource("submit/"), json={'task': task_json})
    if resp.status_code != requests.codes.okay:
        print("Something bad happened")

# Used to tell if the workflow is currently paused
# Will eventually be moved to a Workflow class
workflow_paused = False
saved_task = None

# Save a task when we pause
def save_task(task):
    global saved_task 
    print(f"Saving {task.name}")
    saved_task = task

def resume():
    global saved_task
    if saved_task is not None:
        submit_task(saved_task)
    # Clear out the saved task
    saved_task = None

# This class is where we act on existing jobs
class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    # Start Job
    def post(self, wf_id):
        # Send tasks to the task manager
        # Get first task and send it to the task manager
        task = list(wfi.get_dependent_tasks(wfi.get_task_by_id(0)))[0]
        # Submit task to TM 
        submit_task(task)
        return "Started workflow!"

    # Query Job
    def get(self, wf_id):
        # Check the database for the current status of all the tasks
        (tasks, requirements, hints) = wfi.get_workflow()
        task_status = ""
        for task in tasks:
            if task.name != "bee_init" and task.name != "bee_exit":
                task_status += f"{task.name}--{wfi.get_task_state(task)}\n"
        print("Returned query")
        resp = make_response(jsonify(msg=task_status, status='ok'), 200)
        return resp

    # Cancel Job
    def delete(self, wf_id):
        # Send a request to the task manager to cancel any ongoing tasks 
        resp = requests.delete(_resource())
        if resp.status_code != requests.codes.okay:
            print("Something bad happened")
        # Remove all tasks currently in the database
        wfi.finalize_workflow()
        #wfi.cleanup()
        print("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp
        
    # Pause / Resume Workflow
    def patch(self, wf_id):
        global workflow_paused
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        if option == 'pause':
            workflow_paused = True
            print("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
            return resp
        elif option == 'resume':
            if workflow_paused == True:
                workflow_paused = False  
                resume()
            print("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        else:
            print("Invalid option")
            resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
            return resp

class JobUpdate(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task_id', type=int, location='json', 
                required=True)
        self.reqparse.add_argument('job_state', type=str, location='json', 
                required=True)

    # Update the state of a task from the task manager
    def put(self):
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
                #wfi.cleanup()

            task = remaining_tasks[0] 
            if task.name != 'bee_exit':
                # Take the first task and schedule it 
                # TODO This won't work well for deeply nested workflows
                if workflow_paused:
                    # If we've paused the workflow save the task until we resume
                    save_task(task)
                else:
                    submit_task(task)
            else:
                print("Workflow Completed!")
                wfi.finalize_workflow()
                #wfi.cleanup()
        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp

api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<string:wf_id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')

if __name__ == '__main__':
    flask_app.run(debug=True, port=str(wfm_listen_port))
