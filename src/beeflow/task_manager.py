"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import atexit
import sys
import logging
import hashlib
import socket
import subprocess
from subprocess import PIPE
import jsonpickle
import json
import requests
import threading
import glob
import os
import traceback

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from beeflow.common.config_driver import BeeConfig

# This must be imported before calling other parts of BEE
if len(sys.argv) >= 2:
    bc.init(userconfig=sys.argv[1])
else:
    bc.init()


from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.cli import log
from beeflow.common.build.build_driver import task2arg
from beeflow.common.build_interfaces import build_main
import beeflow.common.log as bee_logging


sys.excepthook = bee_logging.catch_exception


runtime = bc.get('task_manager', 'container_runtime')

tm_listen_port = bc.get('task_manager', 'listen_port')

wfm_listen_port = bc.get('workflow_manager', 'listen_port')

flask_app = Flask(__name__)
api = Api(flask_app)

submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored


def _url():
    """Return  the url to the WFM."""
    workflow_manager = 'bee_wfm/v1/jobs/'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'


def _resource(tag=""):
    """Access the WFM."""
    return _url() + str(tag)


def update_task_state(task_id, job_state, **kwargs):
    """Informs the workflow manager of the current state of a task."""
    data = {'task_id': task_id, 'job_state': job_state}
    if 'metadata' in kwargs:
        metadata_json = jsonpickle.encode(kwargs['metadata'])
        kwargs['metadata'] = metadata_json
    data.update(kwargs)
    resp = requests.put(_resource("update/"),
                        json=data)
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
        if hint.class_ == "DockerRequirement" and "dockerImageId" in hint.params.keys():
            metadata['container_runtime'] = container_runtime
            container_path = hint.params["dockerImageId"]
            with open(container_path, 'rb') as container:
                c_hash = hashlib.md5()
                chunk = container.read(8192)
                while chunk:
                    c_hash.update(chunk)
                    chunk = container.read(8192)
            container_hash = c_hash.hexdigest()
            metadata['container_hash'] = container_hash
    return metadata


def resolve_environment(task):
    """Use build interface to create a valid environment."""
    build_main(bc, task)


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    while len(submit_queue) >= 1:
        # Single value dictionary
        task_dict = submit_queue.pop(0)
        task = next(iter(task_dict.values()))
        try:
            log.info('Resolving environment for task {}'.format(task.name))
            _ = resolve_environment(task)
            log.info('Environment preparation complete for task {}'.format(task.name))
            job_id, job_state = worker.submit_task(task)
            log.info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
            # place job in queue to monitor
            job_queue.append({'task': task, 'job_id': job_id, 'job_state': job_state})
            # Update metadata
            # task_metadata = gen_task_metadata(task, job_id)
            # Need to
            # task_metadata.replace("'", '"')
            # update_task_metadata(task.id, task_metadata)
        except Exception as err:
            # Set job state to failed
            job_state = 'SUBMIT_FAIL'
            log.error(f'Task Manager submit task {task.name} failed! \n {err}')
            log.error(f'{task.name} state: {job_state}')
            # Log the traceback information as well
            log.error(traceback.format_exc())
        finally:
            # Send the initial state to WFM
            # update_task_state(task.id, job_state, metadata=task_metadata)
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
            update_task_state(task.id, job_state, output={})

        if job_state in ('FAILED', 'COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)
            log.info(f'Job {job_id} done {task.name}: removed from job status queue')


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
            except Exception as err:
                log.error(err)
                log.error(traceback.format_exc())
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        job_queue.clear()
        submit_queue.clear()
        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


# This could probably be in a Resource class, but since its only one route
# it seems to be fine right here
@flask_app.route('/status')
def get_status():
    """Report the current status of the Task Manager."""
    # TODO: Report statistics about jobs, perhaps current system load, etc.
    return make_response(jsonify(status='up'), 200)


# WorkerInterface needs to be placed here. Don't Move!
from beeflow.common.worker_interface import WorkerInterface
import beeflow.common.worker as worker_pkg

#try:
#    WLS = bc.userconfig.get('DEFAULT', 'workload_scheduler')
#except ValueError as error:
#    log.error(f'workload scheduler error {error}')
#    WLS = None
WLS = bc.get('DEFAULT', 'workload_scheduler')
worker_class = worker_pkg.find_worker(WLS)
if worker_class is None:
    sys.exit(f'Workload scheduler {WLS}, not supported.\n' +
             f'Please check {bc.userconfig_path()} and restart TaskManager.')
# Get the parameters for the worker classes
worker_kwargs = {
    'bee_workdir': bc.get('DEFAULT', 'bee_workdir'),
    'container_runtime': bc.get('task_manager', 'container_runtime'),
    'job_template': bc.get('task_manager', 'job_template', fallback=None),
    # extra options to be passed to the runner (i.e. srun [RUNNER_OPTS] ... for Slurm)
    'runner_opts': bc.get('task_manager', 'runner_opts', fallback=None),
}
# TODO: Maybe this should be put into a sub class
if WLS == 'Slurm':
    worker_kwargs['slurm_socket'] = bc.get('slurmrestd', 'slurm_socket')
worker = WorkerInterface(worker_class, **worker_kwargs)

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')

if __name__ == '__main__':
    hostname = socket.gethostname()
    log.info(f'Starting Task Manager on host: {hostname}')
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='task_manager.log')
    log.info(f'tm_listen_port:{tm_listen_port}')
    container_runtime = bc.get('task_manager', 'container_runtime')
    log.info(f'container_runtime: {container_runtime}')

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    flask_app.logger.addHandler(handler)
    flask_app.run(debug=False, port=str(tm_listen_port))
# Ignore TODO comments
# Ignoring "modules loaded below top of file" warning per Pat's comment
# Ignoring flask.logger.AddHandler not found because logging is working...
# Ignoring W1202: https://github.com/PyCQA/pylint/issues/2395
# Ignoring W0703: Catching general exception is ok in our case.
# Ignoring C0206: Iterating with .items() is not important for readability or functionality
# pylama:ignore=W0511,E402,C0413,E1101,W1202,W0703,C0206
