#!flask/bin/python
import sys

import beeflow.common.gdb.neo4j_driver as GDB

# Server and REST handling
from flask import Flask
from flask_restful import Resource, Api, reqparse

# Asynchronous workers
from celery import Celery

# Interacting with the rm, tm, and scheduler
import requests

app = Flask(__name__)
app = Api(app)

# Initializes the graph database
gdb = GDB()

# Where we submit jobs
class JobsList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                    help='Need a title',
                                    location='json')
        super(JobsList, self).__init__()

    # Response to Submit Job
    # Submit Workflow
    def post(self, workflow):
        # Add workflow to the neo4j database
        # TODO figure out how to get a file here
        GDB.load_workflow(workflow)
        # ID is going to need to come from the graphDB
        return id

# This class is where we act on existing jobs
class JobActions(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('id', type=str, required=True,
                                    help='Need an ID',
                                    location='json')

    # Start Job
    def put(self, id):
        # Send workflow to the scheduler and start running tasks
        start_wf(id)
        return "Job is starting", 

    # Query Job
    def get(self, id):
        # Ask the scheduler how the workflow is going
        query(id)

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
    # Check with the scheduler on the progress of the workflow
    pass

@celery.task()
def cancel(id):
    # Cancel the workflow with the scheduler
    pass

@celery.task()
def pause(id):
    pass

api.add_resource(JobActions, '/bee_orc/v1/jobs/<int:id>', endpoint = 'jobs')
api.add_resource(JobsList, '/bee_orc/v1/jobs/', endpoint = 'job')

if __name__ == '__main__':
    app.run(debug=True)
