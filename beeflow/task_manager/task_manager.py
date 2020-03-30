"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import time
import atexit
import os
import json

from flask import Flask
from flask_restful import Resource, Api, reqparse, fields

from beeflow.common.data.wf_data import Task
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
from apscheduler.schedulers.background import BackgroundScheduler

flask_app = Flask(__name__)
api = Api(flask_app)

submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored

workflow_manager = 'bee_wfm/v1/jobs'
# Returns the url to the resource
def _url():
    return f'http://127.0.0.1:5050/{task_manager}'

def _resource(tag=""): 
    return _url() + str(tag)

def check_queue():
    while len(submit_queue) >= 1:
        task_dict = submit_queue.pop(0)
        task_id = list(task_dict)[0]
        task = task_dict.get(task_id)
        job_id, job_state = WORKER.submit_task(task)

        # fix TODO prints will become message sends to WFM
        if job_id == -1:
            error = job_state
            job_state = 'SUBMIT_FAIL'
            # send task failed message to WFM
            print('Task failed:', task_id, task.name, job_state, error)
        else:
            # place job in queue to monitor and send intial state to WFM)
            job_queue.append({task_id: {'name': task.name,
                                        'job_id': job_id,
                                        'job_state': job_state}})
            print('Submitted: ', task_id, task.name,
                  'Job:', job_id, job_state)

def update_job_queue():
    """Check and update states of jobs in queue, remove completed jobs."""
    for job in job_queue:
        task_id = list(job)[0]
        current_task = job[task_id]
        job_id = current_task['job_id']
        state = WORKER.query_job(job_id)
        if state[0] == 1:
            job_state = state[1]
        else:
            job_state = 'ZOMBIE'
        if job_state != current_task['job_state']:
            current_task['job_state'] = job_state
            # fix TODO new state event to WFM here
            print('Task changed state:', task_id, current_task['name'],
                  job_id, job_state)
        # fix TODO needs to be an abstract state see wiki for our TM states
        if job_state in ('COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # fix TODO create event Send job info to WFM
            print('Job done:', task_id, current_task['name'], job_id,
                  job_state)
            job_queue.remove(job)


def check_tasks():
    check_queue()
    update_job_queue()

# TODO Decide on the time interval for the scheduler currently just does 1
# This code block runs
scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
scheduler.add_job(func=check_tasks, trigger="interval", minutes=1)
scheduler.start()

# This kills the scheduler so we don't accidentally leave a zombie process
atexit.register(lambda: scheduler.shutdown())

class TaskSubmit(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task', type=str, location='json')
    
    # WFM sends a job to the task manager
    def post(self):
        print("Blueblood")
        data = self.reqparse.parse_args()
        print(data)
        task = data['task']


class TaskActions(Resource):
    def __init(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='tasks')

        # Cancel Task
        def delete(self):
            cancel_task()

WORKER = WorkerInterface(SlurmWorker)

def read_task(json_file):
    """Get task from json file, will come from WFM."""
    with open(json_file) as json_f:
        sent_task = json.load(json_f)
        os.remove(json_file)
        task_cmd = sent_task['command'].split(',')
        # fix TODO submit does not use hints and subworkflow
        # fix TODO task_id should be part of task will it be?
        task = Task(name=sent_task['name'],
                    command=task_cmd,
                    hints=None,
                    subworkflow=None,
                    inputs=sent_task['inputs'],
                    outputs=sent_task['outputs'])
        task_id = sent_task['task_id']
        return task, task_id


def receive_task(json_file, submit_queue):
    """Recieve task from WFM, place it in queue to submit."""
    # for now read it from a file TODO function REST event to submit task
    if os.path.exists(json_file):
        task, task_id = read_task(json_file)
        submit_queue.append({task_id: task})


def cancel_task(json_file, job_queue):
    """Received from WFM to cancel job, add to queue to monitor state."""
    # for now read it from a file TODO function for REST event to cancel task
    if os.path.exists(json_file):
        with open(json_file) as json_f:
            cancel_t = json.load(json_f)
            os.remove(json_file)
            success, job_state = WORKER.cancel_job(cancel_t["job_id"])
        if success == 1:
            job_queue.append({cancel_t['task_id']:
                             {'name': cancel_t['name'],
                              'job_id': cancel_t['job_id'],
                              'job_state': job_state}})
        else:
            # fix TODO prints should send event to REST for state change
            print('Cancel failed:',
                  cancel_t['task_id'], cancel_t['name'], job_state)


api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/<int:wf_id>')

if __name__ == '__main__':
        flask_app.run(debug=True, port='5050')
