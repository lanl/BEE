"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import atexit
import sys
import jsonpickle
import requests

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.config.config_driver import BeeConfig
from apscheduler.schedulers.background import BackgroundScheduler

bc = BeeConfig()
if bc.userconfig.has_section('task_manager'):
    tm_listen_port = bc.userconfig['task_manager'].get('listen_port', '5050')
else:
    print("[task_manager] section not found in configuration file, default values added")

    tm_dict = {
        'name': 'task_manager',
        'listen_port': '5050',
    }

    bc.add_section('user', tm_dict)

    sys.exit("Please check " + str(bc.userconfig_file) + " and restart TaskManager")

if bc.userconfig.has_section('workflow_manager'):
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port', '5000')
else:
    print("[workflow_manager] section not found in configuration, default values added")
    wfm_listen_port = '5000'

flask_app = Flask(__name__)
api = Api(flask_app)

submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored


# Returns the url to the WFM
def _url():
    workflow_manager = 'bee_wfm/v1/jobs/'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'


# Used to access the WFM
def _resource(tag=""):
    return _url() + str(tag)


# Informs the task manager of the current state of a task
def update_task_state(task_id, job_state):
    resp = requests.put(_resource("update/"),
                        json={'task_id': task_id, 'job_state': job_state})
    if resp.status_code != requests.codes.okay:
        print("WFM not responding")
    else:
        print('Updated task!')


# Submits all jobs currently in submit queue to slurm
def submit_jobs():
    while len(submit_queue) >= 1:
        # Single value dictionary
        temp = submit_queue.pop(0)
        task_id = list(temp)[0]
        task = temp[task_id]
        job_id, job_state = WORKER.submit_task(task)

        if job_id == -1:
            # Set job state to failed message
            job_state = 'SUBMIT_FAIL'
        else:
            # place job in queue to monitor and send initial state to WFM
            print(f'Job Submitted: job_id: {job_id} job_state: {job_state}')
            job_queue.append({task_id: {'name': task.name,
                                        'job_id': job_id,
                                        'job_state': job_state}})
        # Send the initial state to WFM
        update_task_state(task_id, job_state)


# Check and update states of jobs in queue, remove completed jobs.
def update_jobs():
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
            print(f'{current_task["name"]} {current_task["job_state"]} -> {job_state}')
            current_task['job_state'] = job_state
            update_task_state(task_id, job_state)
        # TODO Make an abstract state see wiki for our TM states
        if job_state in ('COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)


# Looks for newly submitted jobs and updates the status of scheduled jobs
def check_tasks():
    submit_jobs()
    update_jobs()


# TODO Decide on the time interval for the scheduler
scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
scheduler.add_job(func=check_tasks, trigger="interval", seconds=5)
scheduler.start()

# This kills the scheduler when the process terminates
# so we don't accidentally leave a zombie process
atexit.register(lambda: scheduler.shutdown())


class TaskSubmit(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task', type=str, location='json')

    # WFM sends a task to the task manager
    def post(self):
        data = self.reqparse.parse_args()
        # Gets a task object
        # TODO Decide whether we want to pass around Task objects or just json
        task = jsonpickle.decode(data['task'])
        # Add the task to the submit queue
        submit_queue.append({task.id: task})
        print(f"Added {task.name} to the submit queue")
        #print(f"task.hints {task.hints} ")
        resp = make_response(jsonify(msg='Task Added!', status='ok'), 200)
        return resp


class TaskActions(Resource):

    # Cancel Task
    def delete(self):
        """Received from WFM to cancel job, add to queue to monitor state."""
        # States which jobs cancelled successfully
        cancel_msg = ""

        for job in job_queue:
            task_id = list(job.keys())[0]
            job_id = job[task_id]['job_id']
            name = job[task_id]['name']

            job_queue.remove(job)
            print(f"Cancelling {name} with job_id: {job_id}")
            success, job_state = WORKER.cancel_job(job_id)
            cancel_msg += f"{name} {task_id} {success} {job_id}"

        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


WORKER = WorkerInterface(SlurmWorker)

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')


if __name__ == '__main__':
    flask_app.run(debug=True, port=str(tm_listen_port))
