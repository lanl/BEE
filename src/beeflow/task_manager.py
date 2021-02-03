"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import configparser
import atexit
import sys
import jsonpickle
import requests

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging
import logging

if len(sys.argv) > 2:
    bc = BeeConfig(userconfig=sys.argv[1])
else:
    bc = BeeConfig()


def check_crt_config(container_runtime):
    """Check container runtime configurations."""
    supported_runtimes = ['Charliecloud', 'Singularity']
    if container_runtime not in supported_runtimes:
        sys.exit(f'Container runtime, {runtime}, not supported.\n' +
                 f'Please check {bc.userconfig_file} and restart TaskManager.')

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
            except configparser.NoOptionError:
                bc.modify_section('user', 'charliecloud', {'image_mntdir': '/tmp'})


# Check task_manager and container_runtime sections of user configuration file
tm_dict = {}
tm_default = {'listen_port': bc.default_tm_port,
              'container_runtime': 'Charliecloud'}
if bc.userconfig.has_section('task_manager'):
    # Insert defaults for any options not in task_manager section of userconfig file
    UPDATE_CONFIG = False
    items = bc.userconfig.items('task_manager')
    for key, value in items:
        tm_dict.setdefault(key, value)
    for key in tm_default:
        if key not in tm_dict.keys():
            tm_dict[key] = tm_default[key]
            UPDATE_CONFIG = True
    if UPDATE_CONFIG:
        bc.modify_section('user', 'task_manager', tm_dict)
else:
    tm_listen_port = bc.default_tm_port
    bc.modify_section('user', 'task_manager', tm_default)
    check_crt_config(tm_default['container_runtime'])
    sys.exit(f'[task_manager] section missing in {bc.userconfig_file}\n' +
             'Default values added. Please check and restart Task Manager.')
runtime = bc.userconfig.get('task_manager', 'container_runtime')
check_crt_config(runtime)

tm_listen_port = bc.userconfig.get('task_manager', 'listen_port')

# Check Workflow manager port, use default if none.
if bc.userconfig.has_section('workflow_manager'):
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',
                                                            bc.default_wfm_port)
else:
    wfm_listen_port = bc.default_wfm_port

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
        print('Updated task state!')


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    while len(submit_queue) >= 1:
        # Single value dictionary
        task_dict = submit_queue.pop(0)
        for task_id, task in task_dict.items():
            try:
                job_id, job_state = worker.submit_task(task)
            except Exception as error:
                # Set job state to failed message
                job_state = 'SUBMIT_FAIL'
                print(f'Task Manager submit task {task.name} failed! \n {error}')
                print(f'{task.name} state: {job_state}')
            else:
                # place job in queue to monitor and send initial state to WFM
                log.step_info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
                job_queue.append({task_id: {'name': task.name,
                                 'job_id': job_id, 'job_state': job_state}})
        # Send the initial state to WFM
        update_task_state(task_id, job_state)


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    for job in job_queue:
        task_id = list(job)[0]
        current_task = job[task_id]
        job_id = current_task['job_id']
        job_state = worker.query_task(job_id)

        if job_state != current_task['job_state']:
            log.step_info(f'{current_task["name"]} {current_task["job_state"]} -> {job_state}')
            current_task['job_state'] = job_state
            update_task_state(task_id, job_state)
        if job_state in ('COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)


def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    submit_jobs()
    update_jobs()


if "pytest" not in sys.modules:
    # TODO Decide on the time interval for the scheduler
    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
    scheduler.add_job(func=process_queues, trigger="interval", seconds=5)
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
        print(f"Added {task.name} task to the submit queue")
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
            print(f"Cancelling {name} with job_id: {job_id}")
            try:
                job_state = worker.cancel_task(job_id)
            except Exception as error:
                print(error)
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        job_queue.clear()
        submit_queue.clear()
        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


# WorkerInterface needs to be placed here. Don't Move!
from beeflow.common.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.worker.lsf_worker import LSFWorker

supported_workload_schedulers = {'Slurm', 'LSF'}
try:
    WLS = bc.userconfig.get('DEFAULT', 'workload_scheduler')
except ValueError as error:
    print(f'workload scheduler error {error}')
    WLS = None
if WLS not in supported_workload_schedulers:
    sys.exit(f'Workload scheduler {WLS}, not supported.\n' +
             f'Please check {bc.userconfig_file} and restart TaskManager.')
if WLS == 'Slurm':
    worker = WorkerInterface(SlurmWorker,
                             slurm_socket=bc.userconfig.get('slurmrestd', 'slurm_socket'),
                             bee_workdir=bc.userconfig.get('DEFAULT', 'bee_workdir'),
                             container_runtime=bc.userconfig.get('task_manager',
                                                                 'container_runtime'),
                             job_template=bc.userconfig.get('task_manager',
                                                            'job_template', fallback=None))

elif WLS == 'LSF':
    worker = WorkerInterface(LSFWorker,
                             bee_workdir=bc.userconfig.get('DEFAULT', 'bee_workdir'),
                             container_runtime=bc.userconfig.get('task_manager',
                                                                 'container_runtime'),
                             job_template=bc.userconfig.get('task_manager',
                                                            'job_template', fallback=None))

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')

if __name__ == '__main__':
    handler = bee_logging.save_log(bc, log, logfile='task_manager.log')
    log.info(f'tm_listen_port:{tm_listen_port}')
    container_runtime = bc.userconfig.get('task_manager', 'container_runtime')
    log.info(f'container_runtime:{container_runtime}')

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
