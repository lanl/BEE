#!flask/bin/python
import os

# Server and REST handling
from flask import Flask
from flask_restful import Resource, Api, reqparse

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

wf = WorkflowInterface()

no_file_resp = {
    'msg':'No file found',
    'status':'error'
}

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
        # Get the id for the workflow
        # Return the id and success
        return {'id': id}, 201

# Add workflow to the database
def add_workflow():
    wf.add_task("ECHO", command=["echo", '"It\'s alive!"'],
            inputs={""}, outputs={""})

class JobSubmit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='files')

    # Client Submits workflow 
    def put(self, id):
        data = self.reqparse.parse_args()
        if data['workflow'] == "":
            return no_file_resp, 201
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
            resp = {'msg':'Workflow uploaded', 'status':'ok'}
            return resp, 201
        else:
            return 200


# This class is where we act on existing jobs
class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='files')

    # Start Job
    def put(self, id):
        # Send workflow to the scheduler and start running tasks
        start_wf(id)
        return "Job is starting"

    # Query Job
    def get(self, id):
        # Ask the scheduler how the workflow is going
        #scheduler_query(id)
        pass

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

api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobSubmit, '/bee_wfm/v1/jobs/submit/<int:id>')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<int:id>')

if __name__ == '__main__':
    flask_app.run(debug=True)


