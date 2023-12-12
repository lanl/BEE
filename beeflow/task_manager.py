"""Task Manager submits & manages tasks from Work Flow Manager.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import atexit
import sys
import hashlib
import os
from pathlib import Path
import re
import socket
import traceback
import jsonpickle

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging
from beeflow.common.build_interfaces import build_main
from beeflow.common.worker_interface import WorkerInterface
from beeflow.common.connection import Connection
import beeflow.common.worker as worker_pkg
from beeflow.common.db import tm_db
from beeflow.common.db.bdb import connect_db
from beeflow.common import paths


log = bee_logging.setup(__name__)

runtime = bc.get('task_manager', 'container_runtime')


flask_app = Flask(__name__)
api = Api(flask_app)

bee_workdir = bc.get('DEFAULT', 'bee_workdir')
db_path = bee_workdir + '/' + 'tm.db'


def _url():
    """Return  the url to the WFM."""
    # Saving this for whenever we need to run jobs across different machines
    # workflow_manager = 'bee_wfm/v1/jobs/'
    # #wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    # wfm_listen_port = wf_db.get_wfm_port()
    # return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'
    return 'bee_wfm/v1/jobs/'


def _resource(tag=""):
    """Access the WFM."""
    return _url() + str(tag)


def _wfm_conn():
    """Get a new connection to the WFM."""
    return Connection(paths.wfm_socket())


def update_task_state(workflow_id, task_id, job_state, **kwargs):
    """Informs the workflow manager of the current state of a task."""
    data = {'wf_id': workflow_id, 'task_id': task_id, 'job_state': job_state}
    if 'metadata' in kwargs:
        kwargs['metadata'] = jsonpickle.encode(kwargs['metadata'])

    if 'task_info' in kwargs:
        kwargs['task_info'] = jsonpickle.encode(kwargs['task_info'])

    data.update(kwargs)
    conn = _wfm_conn()
    resp = conn.put(_resource("update/"), json=data)
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
    hostname = socket.gethostname()
    metadata = {'job_id': job_id, 'host': hostname}
    for hint in task.hints:
        if hint.class_ == "DockerRequirement" and "dockerImageId" in hint.params.keys():
            metadata['container_runtime'] = bc.get('task_manager', 'container_runtime')
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
    build_main(task)


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    db = connect_db(tm_db, db_path)
    while db.submit_queue.count() >= 1:
        # Single value dictionary
        task = db.submit_queue.pop()
        try:
            log.info(f'Resolving environment for task {task.name}')
            resolve_environment(task)
            log.info(f'Environment preparation complete for task {task.name}')
            job_id, job_state = worker.submit_task(task)
            log.info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
            # place job in queue to monitor
            db.job_queue.push(task=task, job_id=job_id, job_state=job_state)
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
            update_task_state(task.workflow_id, task.id, job_state)


def get_task_checkpoint(task):
    """Harvest task checkpoint."""
    task_checkpoint = None
    hints = dict(task.hints)
    try:
        # Try to get Hints
        hint_checkpoint = hints['beeflow:CheckpointRequirement']
    except (KeyError, TypeError):
        # Task Hints are not mandatory. No task checkpoint hint specified.
        hint_checkpoint = None
    try:
        # Try to get Requirements
        req_checkpoint = task.requirements['beeflow:CheckpointRequirement']
    except (KeyError, TypeError):
        # Task Requirements are not mandatory. No task checkpoint requirement specified.
        req_checkpoint = None
    # Prefer requirements over hints
    if req_checkpoint:
        task_checkpoint = req_checkpoint
    elif hint_checkpoint:
        task_checkpoint = hint_checkpoint
    return task_checkpoint


def get_restart_file(task_checkpoint, task_workdir):
    """Find latest checkpoint file."""
    if 'file_regex' not in task_checkpoint:
        raise RuntimeError('file_regex is required for checkpointing')
    if 'file_path' not in task_checkpoint:
        raise RuntimeError('file_path is required for checkpointing')
    file_regex = task_checkpoint['file_regex']
    file_path = Path(task_workdir, task_checkpoint['file_path'])
    regex = re.compile(file_regex)
    checkpoint_files = [
        Path(file_path, fname) for fname in os.listdir(file_path)
        if regex.match(fname)
    ]
    checkpoint_files.sort(key=os.path.getmtime)
    try:
        checkpoint_file = checkpoint_files[-1]
        return str(checkpoint_file)
    except IndexError:
        raise RuntimeError('Missing checkpoint file for task') from None


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    db = connect_db(tm_db, db_path)
    # Need to make a copy first
    job_q = list(db.job_queue)
    for job in job_q:
        id_ = job.id
        task = job.task
        job_id = job.job_id
        job_state = job.job_state
        new_job_state = worker.query_task(job_id)

        # If state changes update the WFM
        if job_state != new_job_state:
            db.job_queue.update_job_state(id_, new_job_state)
            if new_job_state in ('FAILED', 'TIMELIMIT', 'TIMEOUT'):
                # Harvest lastest checkpoint file.
                task_checkpoint = get_task_checkpoint(task)
                log.info(f'state: {new_job_state}')
                log.info(f'TIMELIMIT/TIMEOUT task_checkpoint: {task_checkpoint}')
                if task_checkpoint:
                    checkpoint_file = get_restart_file(task_checkpoint, task.workdir)
                    task_info = {'checkpoint_file': checkpoint_file, 'restart': True}
                    update_task_state(task.workflow_id, task.id, new_job_state,
                                      task_info=task_info)
                else:
                    update_task_state(task.workflow_id, task.id, new_job_state)
            else:
                update_task_state(task.workflow_id, task.id, new_job_state)

        if job_state in ('ZOMBIE', 'COMPLETED', 'CANCELLED', 'FAILED', 'TIMEOUT', 'TIMELIMIT'):
            # Remove from the job queue. Our job is finished
            db.job_queue.remove_by_id(id_)


def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    submit_jobs()  # noqa
    update_jobs()  # noqa


if "pytest" not in sys.modules:
    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
    scheduler.add_job(func=process_queues, trigger="interval", seconds=30)
    scheduler.start()

    # This kills the scheduler when the process terminates
    # so we don't accidentally leave a zombie process
    atexit.register(scheduler.shutdown)


class TaskSubmit(Resource):
    """WFM sends tasks to the task manager."""

    def __init__(self):
        """Intialize request."""

    @staticmethod
    def post():
        """Receives task from WFM."""
        db = connect_db(tm_db, db_path)
        parser = reqparse.RequestParser()
        parser.add_argument('tasks', type=str, location='json')
        data = parser.parse_args()
        tasks = jsonpickle.decode(data['tasks'])
        for task in tasks:
            db.submit_queue.push(task)
            log.info(f"Added {task.name} task to the submit queue")
        resp = make_response(jsonify(msg='Tasks Added!', status='ok'), 200)
        return resp


class TaskActions(Resource):
    """Actions to take for tasks."""

    @staticmethod
    def delete():
        """Cancel received from WFM to cancel job, update queue to monitor state."""
        db = connect_db(tm_db, db_path)
        cancel_msg = ""
        for job in db.job_queue:
            task_id = job.task.id
            job_id = job.job_id
            name = job.task.name
            log.info(f"Cancelling {name} with job_id: {job_id}")
            try:
                job_state = worker.cancel_task(job_id)
            except Exception as err:
                log.error(err)
                log.error(traceback.format_exc())
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        db.job_queue.clear()
        db.submit_queue.clear()
        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp


# This could probably be in a Resource class, but since its only one route
# it seems to be fine right here
@flask_app.route('/status')
def get_status():
    """Report the current status of the Task Manager."""
    return make_response(jsonify(status='up'), 200)


WLS = bc.get('DEFAULT', 'workload_scheduler')
worker_class = worker_pkg.find_worker(WLS)
if worker_class is None:
    sys.exit(f'Workload scheduler {WLS}, not supported.\n'
             + f'Please check {bc.userconfig_path()} and restart TaskManager.')
# Get the parameters for the worker classes
worker_kwargs = {
    'bee_workdir': bc.get('DEFAULT', 'bee_workdir'),
    'container_runtime': bc.get('task_manager', 'container_runtime'),
    # extra options to be passed to the runner (i.e. srun [RUNNER_OPTS] ... for Slurm)
    'runner_opts': bc.get('task_manager', 'runner_opts'),
}
# Job defaults
for default_key in ['default_account', 'default_time_limit', 'default_partition']:
    worker_kwargs[default_key] = bc.get('job', default_key)
# Special slurm arguments
if WLS == 'Slurm':
    worker_kwargs['use_commands'] = bc.get('slurm', 'use_commands')
    worker_kwargs['slurm_socket'] = paths.slurm_socket()
    worker_kwargs['openapi_version'] = bc.get('slurm', 'openapi_version')
worker = WorkerInterface(worker_class, **worker_kwargs)

api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
api.add_resource(TaskActions, '/bee_tm/v1/task/')

# if __name__ == '__main__':
#    hostname = socket.gethostname()
#    log.info(f'Starting Task Manager on host: {hostname}')
#    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
#    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='task_manager.log')
#    log.info(f'tm_listen_port:{tm_listen_port}')
#    container_runtime = bc.get('task_manager', 'container_runtime')
#    log.info(f'container_runtime: {container_runtime}')
#
#    # Werkzeug logging
#    werk_log = logging.getLogger('werkzeug')
#    werk_log.setLevel(logging.INFO)
#    werk_log.addHandler(handler)
#
#    # Flask logging
#    flask_app.logger.addHandler(handler)
#    flask_app.run(debug=False, port=str(tm_listen_port))

# Ignoring W0703: Catching general exception is ok for failed submit and cancel.
# Ignoring E402: "module level import is not at top of file" - this is required
#                for the bee config
# pylama:ignore=W0703,E402
