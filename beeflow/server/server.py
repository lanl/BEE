#!flask/bin/python3
import os
import jsonpickle
import requests

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



wfi = WorkflowInterface()

# Where we submit jobs
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
        name = data['title']
        print("Job name is " + name)
        # Get the wf_id for the workflow
        # Return the wf_id and success
        resp = make_response(jsonify(wf_id="42"), 201)
        return resp

# Add workflow to the database
def add_workflow(filename):
    tasks = []
    task_input = 'grep.in'
    task_output = 'grep.out'
    grep_string = 'database'
    tasks.append(wfi.add_task(
            'GREP', command=['grep', '-i', grep_string , task_input, '>', task_output],
                inputs={task_input}, outputs={task_output}))

    task_input = 'grep.out'
    task_output = 'wc.out'
    tasks.append(wfi.add_task(
            'WC', command=['wc', '-l', task_input, '>', task_output],
                inputs={task_input}, outputs={task_output}))
    wfi.load_workflow(wf)
    wfi.initialize_workflow()

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
        workflow = data['workflow']

        if workflow:
            workflow = data['workflow']
            print(workflow)
            # TODO get the filename
            filename = "echo.cwl"
            workflow.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], filename))

            # Parse the workflow and add it to the database
            add_workflow(filename)
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
    def put(self, wf_id):
        # Send tasks to the task manager
        # Get tasks from the neo4j database
        task = get_dependent_task()
        # Serialize task with json
        task_msg = jsonpickle.encode(task)
        # Send task_msg to task manager
        resp = requests.put(_resource("http://127.0.0.1:5000/{task_manager}"))
        if resp.status_code != requests.codes.okay:
            print("Something bad happened")

    # Query Job
    def get(self, wf_id):
        # Ask the scheduler how the workflow is going
        resp = requests.get(_resource("http://127.0.0.1:5000/{task_manager}"))
        if resp.status_code != requests.codes.okay:
            print("Something bad happened")

    # Cancel Job
    def delete(self, wf_id):
        # Send a request to the scheduler to cancel the workflow
        # Also need to send a request to the task manager to cancel any ongoing tasks 
        # Scheduler should return which of the tasks are still running
        pass
        
    ## Pause Job
    # Not currently implemented
    #def patch(self, wf_id):
    #    # Send a request to the scheduler to pause the workflow
    #    # Just like with cancel we need to work this out between the TM and sched
    #    pass


api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<int:wf_id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<int:wf_id>')

if __name__ == '__main__':
    flask_app.run(debug=True, port='5000')


