"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import configparser
import atexit
import sys
import logging
import hashlib
import socket
import jsonpickle
import requests
import time

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging

if len(sys.argv) > 2:
    bc = BeeConfig(userconfig=sys.argv[1])
else:
    bc = BeeConfig()


def check_crt_config(c_runtime):
    """Check container runtime configurations."""
    supported_runtimes = ['Charliecloud', 'Singularity']
    if c_runtime not in supported_runtimes:
        sys.exit(f'Container runtime, {runtime}, not supported.\n' +
                 f'Please check {bc.userconfig_file} and restart TaskManager.')

    if c_runtime == 'Charliecloud':
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
# Get Task Manager resource information
# TODO: This may need to be determined dynamically on certain systems
tm_nodes = bc.userconfig['task_manager'].get('nodes', 1)

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


def _wfm():
    """Return the base url for the WFM."""
    return f'http://127.0.0.1:{wfm_listen_port}'


def _url():
    """Return the url to the WFM."""
    workflow_manager = 'bee_wfm/v1/jobs/'
    return f'{_wfm()}/{workflow_manager}'


def _resource(tag=""):
    """Access the WFM."""
    return _url() + str(tag)


def update_task_state(task_id, job_state):
    """Informs the workflow manager of the current state of a task."""
    resp = requests.put(_resource("update/"),
                        json={'task_id': task_id, 'job_state': job_state})
    if resp.status_code != 200:
        log.warning("WFM not responding when sending task update.")


def update_task_metadata(task_id, metadata):
    """Send workflow manager task metadata."""
    log.info(f'Update task metadata for {task_id}:\n {metadata}')
    # resp = requests.put(_resource("update/"), json=metadata)
    # if resp.status_code != 200:
    #     log.warning("WFM not responding when sending task metadata.")


def gen_task_metadata(task, job_id):
    """Generate dictionary of task metadata for the job submitted.

    Includes:
       job_id
       hostname
       container runtime (when task uses a container)
       hash of container file (when task uses a container)
    """
    metadata = {'job_id': job_id, 'host': hostname}
    for hint in task.hints:
        req_class, req_key, req_value = hint
        if req_class == "DockerRequirement" and req_key == "dockerImageId":
            metadata['container_runtime'] = container_runtime
            container_path = req_value
            with open(container_path, 'rb') as container:
                c_hash = hashlib.md5()
                chunk = container.read(8192)
                while chunk:
                    c_hash.update(chunk)
                    chunk = container.read(8192)
            container_hash = c_hash.hexdigest()
            metadata['container_hash'] = container_hash
    return metadata


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    while len(submit_queue) >= 1:
        # Single value dictionary
        task_dict = submit_queue.pop(0)
        task = next(iter(task_dict.values()))
        try:
            job_id, job_state = worker.submit_task(task)
            log.info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
            # place job in queue to monitor
            job_queue.append({'task': task, 'job_id': job_id, 'job_state': job_state})
            # Update metadata
            task_metadata = gen_task_metadata(task, job_id)
            update_task_metadata(task.id, task_metadata)
        except Exception as error:
            # Set job state to failed
            job_state = 'SUBMIT_FAIL'
            log.error(f'Task Manager submit task {task.name} failed! \n {error}')
            log.error(f'{task.name} state: {job_state}')
        finally:
            # Send the initial state to WFM
            update_task_state(task.id, job_state)


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    for job in job_queue:
        task = job['task']
        job_id = job['job_id']
        job_state = worker.query_task(job_id)

        if job_state != job['job_state']:
            log.info(f'{task.name} {job["job_state"]} -> {job_state}')
            job['job_state'] = job_state
            update_task_state(task.id, job_state)

        if job_state in ('FAILED', 'COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)
            log.info(f'Job {job_id} done {task.name}: removed from job status queue')


def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    submit_jobs()
    update_jobs()


last_status_check = None


def call_wfm():
    """Call the WFM, if necessary (makes a POST request).

    This is used to let the WFM know about this Task manager.
    """
    global last_status_check
    t = int(time.time())
    if last_status_check is None or last_status_check < (t - 200):
        data = {
            'tm_listen_host': 'localhost',
            'tm_listen_port': tm_listen_port,
            'resource': {
                'nodes': tm_nodes,
                # TODO: Other resource properties
            },
        }
        log.info('Posting TM info to the WFM')
        # POST TM info to the Workflow Manager
        try:
            resp = requests.post(f'{_wfm()}/bee_wfm/v1/task_managers/', json=data)
            if not resp.ok:
                log.error('WFM not responding')
            else:
                last_status_check = t
        except requests.exceptions.ConnectionError:
            log.error('Cannot connect to WFM')


if "pytest" not in sys.modules:
    # TODO Decide on the time interval for the scheduler
    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
    scheduler.add_job(func=process_queues, trigger="interval", seconds=5)
    scheduler.add_job(func=call_wfm, trigger="interval", seconds=20)
    scheduler.start()

    # This kills the scheduler when the process terminates
    # so we don't accidentally leave a zombie process
    atexit.register(lambda x: scheduler.shutdown())


class TaskSubmit(Resource):
    """WFM sends tasks to the task manager."""

    def __init__(self):
        """Intialize request."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('tasks', type=str, location='json')

    def post(self):
        """Receives task from WFM."""
        data = self.reqparse.parse_args()
        tasks = jsonpickle.decode(data['tasks'])
        for task in tasks:
            submit_queue.append({task.id: task})
            log.info(f"Added {task.name} task to the submit queue")
        resp = make_response(jsonify(msg='Tasks Added!', status='ok'), 200)
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
            log.info(f"Cancelling {name} with job_id: {job_id}")
            try:
                job_state = worker.cancel_task(job_id)
            except Exception as error:
                log.error(error)
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        job_queue.clear()
        submit_queue.clear()
        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


# WorkerInterface needs to be placed here. Don't Move!
from beeflow.common.worker_interface import WorkerInterface
import beeflow.common.worker as worker


try:
    WLS = bc.userconfig.get('DEFAULT', 'workload_scheduler')
except ValueError as error:
    log.error('workload_scheduler option not found for the Task Manager')
    sys.exit(1)
try:
    worker_class = worker.worker_classes[WLS]
except KeyError:
    sys.exit('Invalid worker "{}"'.format(WLS))
worker = WorkerInterface(worker_class, bee_workdir=bc.userconfig.get('DEFAULT', 'bee_workdir'),
                         container_runtime=bc.userconfig.get('task_manager', 'container_runtime'),
                         job_template=bc.userconfig.get('task_manager', 'job_template',
                                                        fallback=None))

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')

if __name__ == '__main__':
    hostname = socket.gethostname()
    log.info(f'Starting Task Manager on host: {hostname}')
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='task_manager.log')
    log.info(f'tm_listen_port:{tm_listen_port}')
    container_runtime = bc.userconfig.get('task_manager', 'container_runtime')
    log.info(f'container_runtime: {container_runtime}')

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
