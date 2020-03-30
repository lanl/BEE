#!flask/bin/python3
import os
import jsonpickle
import requests
import random
import cwl_utils.parser_v1_0 as cwl
import beeflow.common.parser.parse_cwl as parser

# Server and REST handling
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

# Asynchronous workers
#from celery_setup import make_celery

# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage

from beeflow.common.wf_interface import WorkflowInterface

flask_app = Flask(__name__)
# Setup celery 
#flask_app.config.update(
#    CELERY_BROKER_URL='redis://localhost:6379',
#    CELERY_RESULT_BACKEND='redis://localhost:6379'
#)

#celery = make_celery(flask_app)
api = Api(flask_app)

UPLOAD_FOLDER = 'workflows'
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Returns the url to the resource
task_manager = "/bee_tm/v1/task/"

def _url():
    return f'http://127.0.0.1:5050/{task_manager}'

def _resource(tag=""): 
    return _url() + str(tag)


wfi = WorkflowInterface()

# Add workflow to the database
def add_workflow(cwl_file):
    top = cwl.load_document(cwl_file)
    parser.create_workflow(top, wfi)
    parser.verify_workflow(wfi)

# Contains the data for the current workflow
# Does not currently work
#class Workflow():
#    def __init__(self, title, filename):
#        # Filename for the workflow
#        self.title = title
#        self.filename = filename
#        self.id = str(random.randint(1, 100))

# TODO make this behave better
# I only want this to be initialized in the workflow submit step

# User says they are going to submit a workflow and 
class JobsList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                    help='Need a title',
                                    location='json')
        super(JobsList, self).__init__()

    # Client sends workflow 
    def post(self):
        data = self.reqparse.parse_args()
        title = data['title']
        # Return the wf_id and success
        resp = make_response(jsonify(wf_id="42"), 201)
        return resp

class JobSubmit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='files')

    # Client Submits workflow 
    def put(self, wf_id):
        data = self.reqparse.parse_args()
        print("Getting workflow")
        if data['workflow'] == "":
            return {'msg':'No file found','status':'error'}, 201

        # Workflow file
        print(data)
        cwl_file = data['workflow']
        print(cwl_file)
        if cwl_file:
            # TODO get the filename
            cwl_file.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], "work.cwl"))
            # Parse the workflow and add it to the database
            # This is jut work.cwl until I can find a way to use the workflow class
            add_workflow("./workflows/work.cwl")
            resp = make_response(jsonify(msg='Workflow uploaded', status='ok'), 201)
            return resp
            #return resp, 201
        else:
            return 200


# This class is where we act on existing jobs
class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='files')

    # Start Job
    def post(self, wf_id):
        # Send tasks to the task manager
        # Get first task and send it to the task manager
        task = wfi.get_dependent_tasks(wfi.get_task_by_id(0))
        # Serialize task with json
        task_json = jsonpickle.encode(task)
        # Send task_msg to task manager
        resp = requests.post(_resource("submit/"), json={'task': task_json})
        if resp.status_code != requests.codes.okay:
            print("Something bad happened")
        print(resp)
        return "Started workflow!"

    # Update the state of task from the task manager
    def put(self, wf_id):
        # Figure out how to find the task in the databse and change it's state 
        pass

    # Query Job
    def get(self, task_id):
        # Check the database for the current status of all the tasks
        (tasks, requirements, hints) = wfi.get_workflow()
        resp = ""
        for task in tasks:
            resp += f"{t.name}--{wfi.get_task_state(t)}\n"
        return resp

    # Cancel Job
    def delete(self, wf_id):
        # Send a request to the task manager to cancel any ongoing tasks 
        resp = requests.get(_resource("http://127.0.0.1:5000/{task_manager}"))
        if resp.status_code != requests.codes.okay:
            print("Something bad happened")
        # Remove all tasks currently in the database
        wfi.finalize_workflow()
        
    # Pause Job
    def patch(self, wf_id):
        # Stop sending jobs to the task manager
        pass 

api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<int:wf_id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<int:wf_id>')

if __name__ == '__main__':
    flask_app.run(debug=True, port='5000')


