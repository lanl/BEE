"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
from configparser import NoOptionError
import atexit
import sys
import os
import platform
import logging
import jsonpickle
import requests

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.common.config.config_driver import BeeConfig

try:
    bc = BeeConfig(userconfig=sys.argv[1])
except IndexError:
    bc = BeeConfig()

supported_runtimes = ['Charliecloud', 'Singularity']


def check_crt_config(container_runtime):
    """Check container runtime configurations."""
    if container_runtime == 'Charliecloud':
        if not bc.userconfig.has_section('charliecloud'):
            cc_opts = {'setup': 'module load charliecloud',
                       'image_mntdir': '/tmp',
                       'chrun_opts': '--cd /home/$USER'

                       }
            bc.modify_section('user', 'charliecloud', cc_opts)
        else:
            try:
                bc.userconfig.get('charliecloud', 'image_mntdir')
            except NoOptionError:
                bc.modify_section('user', 'charliecloud', {'image_mntdir': '/tmp'})


# Set Task Manager default port, attempt to prevent collisions
TM_PORT = 5050
if platform.system() == 'Windows':
    # Get parent's pid to offset ports. uid method better but not available in Windows
    TM_PORT += os.getppid() % 100
else:
    TM_PORT += os.getuid() % 100

if bc.userconfig.has_section('task_manager'):
    try:
        bc.userconfig.get('task_manager', 'listen_port')
    except NoOptionError:
        bc.modify_section('user', 'task_manager', {'listen_port': TM_PORT})
    try:
        bc.userconfig.get('task_manager', 'container_runtime')
    except NoOptionError:
        bc.modify_section('user', 'task_manager', {'container_runtime': 'Charliecloud'})
    if bc.userconfig.get('task_manager', 'container_runtime') not in supported_runtimes:
        sys.exit('Container Runtime not supported!\n' +
                 f'Please check {bc.userconfig_file} and restart TaskManager.')
    runtime = bc.userconfig.get('task_manager', 'container_runtime')
    check_crt_config(runtime)
else:
    tm_listen_port = TM_PORT
    tm_dict = {'listen_port': tm_listen_port, 'container_runtime': 'Charliecloud'}
    bc.modify_section('user', 'task_manager', tm_dict)
    check_crt_config('Charliecloud')
    sys.exit(f'[task_manager] section missing in {bc.userconfig_file}, ' +
             'default values added.\n Please check and restart Task Manager.')

tm_listen_port = bc.userconfig.get('task_manager', 'listen_port')

# Check Workflow manager port
if bc.userconfig.has_section('workflow_manager'):
    try:
        bc.userconfig.get('workflow_manager', 'listen_port')
    except NoOptionError:
        sys.exit(f'[workflow_manager] missing listen_port in {bc.userconfig_file}')
else:
    sys.exit(f'[workflow_manager] section missing in {bc.userconfig_file}')

wfm_listen_port = bc.userconfig.get('workflow_manager', 'listen_port')

flask_app = Flask(__name__)
api = Api(flask_app)

submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored


def _url():
    """Return the url to the WFM."""
    workflow_manager = 'bee_wfm/v1/jobs/'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'


def _resource(tag=""):
    """Access the WFM."""
    return _url() + str(tag)


def update_task_state(task_id, job_state):
    """Informs the workflow manager of the current state of a task."""
    resp = requests.put(_resource("update/"),
                        json={'task_id': task_id, 'job_state': job_state})
    if resp.status_code != 200:
        print("WFM not responding")
    else:
        print('Updated task!')


def submit_jobs():
    """Submit all jobs currently in submit queue to slurm."""
    while len(submit_queue) >= 1:
        # Single value dictionary
        temp = submit_queue.pop(0)
        task_id = list(temp)[0]
        task = temp[task_id]
        job_id, job_state = worker.submit_task(task)

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


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    for job in job_queue:
        task_id = list(job)[0]
        current_task = job[task_id]
        job_id = current_task['job_id']
        state = worker.query_task(job_id)
        if state[0] == 1:
            job_state = state[1]
        else:
            job_state = 'ZOMBIE'
        if job_state != current_task['job_state']:
            print(f'{current_task["name"]} {current_task["job_state"]} -> {job_state}')
            current_task['job_state'] = job_state
            update_task_state(task_id, job_state)
        if job_state in ('COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)


def check_tasks():
    """Look for newly submitted jobs and updates status of scheduled jobs."""
    submit_jobs()
    update_jobs()


# TODO Decide on the time interval for the scheduler
scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
scheduler.add_job(func=check_tasks, trigger="interval", seconds=5)
scheduler.start()

# This kills the scheduler when the process terminates
# so we don't accidentally leave a zombie process
atexit.register(lambda x: scheduler.shutdown())


class TaskSubmit(Resource):
    """WFM sends task to the task manager."""

    def __init__(self):
        """Intialize request."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task', type=str, location='json')

    def post(self):
        """Receives task from WFM."""
        data = self.reqparse.parse_args()
        task = jsonpickle.decode(data['task'])
        submit_queue.append({task.id: task})
        print(f"Added {task.name} to the submit queue")
        resp = make_response(jsonify(msg='Task Added!', status='ok'), 200)
        return resp


class TaskActions(Resource):
    """Actions to take for tasks."""

    @staticmethod
    def delete():
        """Cancel received from WFM to cancel job, update queue to monitor state."""
        cancel_msg = ""

        for job in job_queue:
            task_id = list(job.keys())[0]
            job_id = job[task_id]['job_id']
            name = job[task_id]['name']

            job_queue.remove(job)
            print(f"Cancelling {name} with job_id: {job_id}")
            success, job_state = worker.cancel_task(job_id)
            cancel_msg += f"{name} {task_id} {success} {job_id} {job_state}"

        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


# WorkerInterface needs to be placed here. Don't Move!
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
worker = WorkerInterface(SlurmWorker,
                         slurm_socket=bc.userconfig.get('slurmrestd', 'slurm_socket'),
                         bee_workdir=bc.userconfig.get('DEFAULT', 'bee_workdir'),
                         container_runtime=bc.userconfig.get('task_manager', 'container_runtime'))

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')


if __name__ == '__main__':
    # Get the parameter for logging
    try:
        bc.userconfig.get('task_manager', 'log')
    except NoOptionError:
        bc.modify_section('user', 'task_manager',
                          {'log': '/'.join([bc.userconfig['DEFAULT'].get('bee_workdir'),
                                            'logs', 'tm.log'])})
    finally:
        tm_log = bc.userconfig.get('task_manager', 'log')
        tm_log = bc.resolve_path(tm_log)
    print('tm_listen_port:', tm_listen_port)
    print('container_runtime', bc.userconfig.get('task_manager', 'container_runtime'))

    handler = logging.FileHandler(tm_log)
    handler.setLevel(logging.DEBUG)

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    flask_app.logger.addHandler(handler)
    flask_app.run(debug=True, port=str(tm_listen_port))
# Ignore TODO comments
# Ignoring "modules loaded below top of file" warning per Pat's comment
# Ignoring flask.logger.AddHandler not found because logging is working...
# pylama:ignore=W0511,E402,C0413,E1101
