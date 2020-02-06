#!flask/bin/python
import os

#import beeflow.common.gdb.neo4j_driver as GDB

# Server and REST handling
from flask import Flask
from flask_restful import Resource, Api, reqparse, fields

# Asynchronous workers
from celery_setup import make_celery

# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage

from beeflow.common.wf_interface import WorkflowInterface

flask_app = Flask(__name__)
# Setup celery 
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)
api = Api(flask_app)

UPLOAD_FOLDER = 'workflows'
flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#wf = WorkflowInterface()
#tasks = []
#workflow = wf.create_workflow(
#        tasks=tasks,
#        requirements={wf.create_requirement("ResourceRequirement", "ramMin", 1024)},
#        hints={wf.create_requirement("ResourceRequirement", "ramMax", 2048)}
#)

#load_workflow(workflow)

# Initializes the graph database
class GDB():
    def load_workflow(self, arg):
        pass

gdb = GDB()

task_fields = {
    'title': fields.String
}

workflows = []

def get_wf_id():
    return 32

# Where we submit jobs
class JobsList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                    help='Need a title',
                                    location='json')
        super(JobsList, self).__init__()

    # Client requests to start a job
    def post(self):
        data = self.reqparse.parse_args()
        name = data['title']
        print("Job name is " + name)
        # Get the id for the workflow
        id = get_wf_id()
        # Return the id and success
        return {'id': id}, 201
    
# This class is where we act on existing jobs
class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='files')

    # Client Submits workflow 
    def post(self, id):
        data = self.reqparse.parse_args()
        if data['workflow'] == "":
            resp = {
                     'msg':'No file found',
                     'status':'error'
                   }
            return resp, 201
        # Workflow file
        workflow = data['workflow']

        if workflow:
            workflow = data['workflow']
            print(workflow)
            # TODO get the filename
            filename = "echo.cwl"
            workflow.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], filename))

            # Add workflow to the neo4j database
            wf.load_workflow()
            resp = {'msg':'Workflow uploaded', 'status':'ok'}
            return resp, 201
        else:
            return 200

         

    # Start Job
    def put(self, id):
        # Send workflow to the scheduler and start running tasks
        start_wf(id)
        return "Job is starting"

    # Query Job
    def get(self, id):
        # Ask the scheduler how the workflow is going
        scheduler_query(id)

    # Cancel Job
    def delete(self, id):
        # Send a request to the scheduler to cancel the workflow
        # Also need to send a request to the task manager to cancel any ongoing tasks 
        # Scheduler should return which of the tasks are still running
        pass

    # Pause Job
    def patch(self, id):
        # Send a request to the scheduler to pause the workflow
        # Just like with cancel we need to work this out between the TM and sched
        pass


@celery.task()
def start_wf(id):
    # Send a request to the scheduler 
    pass

@celery.task()
def query(id):
#    # Check with the scheduler on the progress of the workflow
    pass

@celery.task()
def cancel(id):
#    # Cancel the workflow with the scheduler
    pass

@celery.task()
def pause(id):
    pass

api.add_resource(JobActions, '/bee_wfm/v1/jobs/<int:id>', endpoint = 'jobs')
api.add_resource(JobsList, '/bee_wfm/v1/jobs/', endpoint = 'job')

if __name__ == '__main__':
    flask_app.run(debug=True)


