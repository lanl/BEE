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
import os
import subprocess

import flask
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

from apscheduler.schedulers.background import BackgroundScheduler
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging

if len(sys.argv) == 2:
    bc = BeeConfig(userconfig=sys.argv[1])
else:
    bc = BeeConfig()


# Hack to get debugging working
def info(msg):
    """Print message to stdout for debugging."""
    print(msg)


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
                       'chrun_opts': '--cd /home/$USER',
                       'container_dir': os.getenv('HOME'),
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
tm_nodes = bc.userconfig['task_manager'].getint('nodes', 1)
tm_name = bc.userconfig['task_manager'].get('name', 'local_tm')

# Check Workflow manager port, use default if none.
if bc.userconfig.has_section('workflow_manager'):
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',
                                                            bc.default_wfm_port)
else:
    wfm_listen_port = bc.default_wfm_port

flask_app = Flask(__name__)
api = Api(flask_app)


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


def get_hint(task, hint_class, hint_key):
    """Get a hint for this task (or None if no such hint)."""
    # Based on code in the container runtime classes
    if task.hints is not None:
        for hint in task.hints:
            req_class, key, value = hint
            if req_class == hint_class and key == hint_key:
                return value
    return None


def _write_request_file(fname, resp):
    """Write a request to a file."""
    # Write the file (this iterates over the content to handle large files)
    with open(fname, 'wb') as fp:
        for chunk in resp.iter_content(chunk_size=8192):
            fp.write(chunk)


def _pull_file(fname):
    """Try pulling a file."""
    # If the path already exists, then don't pull anything
    if os.path.exists(fname):
        return
    # TODO: Set the tarball extension in the config file
    tar_ext = 'tar.bz2'
    try:
        # The stream=True argument is required for large files
        resp = requests.get(f'{_wfm()}/bee_wfm/v1/files/{fname}', stream=True)
        if not resp.ok:
            # Check if its a tarred directory
            tarfile = f'{fname}.{tar_ext}'
            resp = requests.get(f'{_wfm()}/bee_wfm/v1/files/{tarfile}', stream=True)
            if not resp.ok:
                log.error('Could not pull file {}'.format(fname))
                return
            _write_request_file(tarfile, resp)
            subprocess.run(['tar', '-xvf', tarfile])
        else:
            _write_request_file(fname, resp)
    except requests.exceptions.ConnectionError:
        log.error('Could not connect to the WFM to pull file {}'.format(fname))


def _send_file_or_dir(fname):
    """Send a file or a directory to the WFM."""
    if os.path.isdir(fname):
        # Put the directory in a tarball (cd to the directory, tar it up, then back out)
        tarball = f'{fname}.tar.bz2'
        cwd = os.getcwd()
        os.chdir(os.path.dirname(fname))
        subprocess.run(['tar', '-cf', tarball, os.path.basename(fname)])
        os.chdir(cwd)
        requests.post(f'{_wfm()}/bee_wfm/v1/files/',
                      files={os.path.basename(tarball): open(tarball, 'rb')})
    elif os.path.isfile(fname):
        requests.post(f'{_wfm()}/bee_wfm/v1/files/',
                      files={os.path.basename(fname): open(fname, 'rb')})


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

container_dir = bc.userconfig.get('charliecloud', 'container_dir')


def complete_job(task):
    """Complete the given job/task."""
    push = get_hint(task, 'Push', 'files')
    # if 'push' in extra_requirements:
    if push is not None:
        # Push files back the WFM
        # XXX: I use '|' as a separator here
        push_files = push.split('|')
        log.info('Pusing files {}'.format(','.join(push_files)))
        for fname in push_files:
            # This checks multiple locations for output files, since
            # stdout results may have been in the cwd of the TM
            try:
                # TODO: Check other directories other than just the home directory.
                home = os.path.expanduser('~/')
                home_fname = os.path.join(home, fname)
                if os.path.exists(fname):
                    # Its in the CWD
                    _send_file_or_dir(fname)
                elif os.path.exists(home_fname):
                    # It's in the home dir
                    _send_file_or_dir(home_fname)
            except requests.exceptions.ConnectionError:
                log.error('Could not connect to the WFM')


def launch_job(task):
    """Launch the given job."""
    log.info('launch_job():')
    # extra_requirements = task_data['extra_requirements']
    # TODO: Check for extra requirements
    log.info('Running presubmit code for task {}'.format(task.name))
    pull_hint = get_hint(task, 'Pull', 'files')
    # submit_queue
    cwd = os.getcwd()
    # if 'pull' in extra_requirements and 'workdir' in extra_requirements:
    if pull_hint is not None:
        # XXX: I use '|' as a separator to allow for lists of files to pull
        pull_files = pull_hint.split('|')
        # XXX: Assume workdir is the user's home directory
        workdir = os.path.expanduser('~/')
        # Change to the current working directory of tasks
        os.chdir(workdir)
        # Pull any files
        for file_ in pull_files:
            log.info('Pulling file {} from the WFM'.format(file_))
            _pull_file(file_)
        os.chdir(cwd)
    return worker.submit_task(task)


# A dict from job_id -> {task_id, job_state} (of the currently running tasks/jobs)
running = {}
# List of task ids in order to run
submit_queue = []
# dict from task_id -> {'task': task, 'allocation': allocation}
task_info = {}

def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    for job_id in running.copy():
        task_id = running[job_id]['task_id']
        old_job_state = running[job_id]['job_state']
        task = task_info[task_id]['task']
        job_state = worker.query_task(job_id)
        running[job_id]['job_state'] = job_state
        if job_state == 'COMPLETED':
            log.info('Task %s completed' % (task.name,))
            complete_job(task)
            # Remove it from the running dict
            del running[job_id]
        # Update the WFM
        if old_job_state != job_state:
            log.info('Task %s: %s -> %s' % (task.name, old_job_state, job_state))
            update_task_state(task.id, job_state)
    # Submit new tasks if we have enough nodes
    while len(running) < tm_nodes and submit_queue:
        task_id = submit_queue.pop(0)
        task = task_info[task_id]['task']
        log.info('Launching new task %s' % (task.name,))
        job_id, job_state = launch_job(task)
        running[job_id] = {
            'task_id': task_id,
            'job_state': job_state,
        }
        # Update the state in the WFM
        update_task_state(task_id, job_state)


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
            'tm_listen_port': int(tm_listen_port),
            'tm_name': tm_name,
            'resource_props': {
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


# Get the interval at which to ping/call the WFM
call_wfm_interval = bc.userconfig['task_manager'].get('call_wfm_interval')
call_wfm_interval = call_wfm_interval if call_wfm_interval is not None else 8


if "pytest" not in sys.modules:
    # TODO Decide on the time interval for the scheduler
    scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
    scheduler.add_job(func=process_queues, trigger="interval", seconds=5)
    scheduler.add_job(func=call_wfm, trigger="interval", seconds=call_wfm_interval)
    scheduler.start()

    # This kills the scheduler when the process terminates
    # so we don't accidentally leave a zombie process
    atexit.register(lambda x: scheduler.shutdown())


class TaskSubmit(Resource):
    """WFM sends tasks to the task manager."""

    def __init__(self):
        """Intialize request."""

    def post(self):
        """Receives task from WFM."""
        log.info('TaskSubmit.post()')
        data = flask.request.json
        for task_id in data:
            # Decode the task
            data[task_id]['task'] = jsonpickle.decode(data[task_id]['task'])
        task_info.update(data)
        # Sort task IDs by ascending time slot and add them to the queue
        task_ids = sorted((task_id for task_id in data), key=lambda task_id: task_info[task_id]['allocation']['time_slot'])
        submit_queue.extend(task_ids)
        resp = make_response(jsonify(msg='Tasks Added!', status='ok'), 200)
        return resp


class TaskActions(Resource):
    """Actions to take for tasks."""

    @staticmethod
    def delete():
        """Cancel received from WFM to cancel job, update queue to monitor state."""
        info('TaskActions.delete()')
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
from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.worker.lsf_worker import LSFWorker
from beeflow.common.worker.simple_worker import SimpleWorker

supported_workload_schedulers = {'Slurm', 'LSF', 'Simple'}
try:
    WLS = bc.userconfig.get('DEFAULT', 'workload_scheduler')
except ValueError as error:
    log.error(f'workload scheduler error {error}')
    WLS = None
if WLS not in supported_workload_schedulers:
    sys.exit(f'Workload scheduler {WLS}, not supported.\n' +
             f'Please check {bc.userconfig_file} and restart TaskManager.')


workload_args = {
    'bee_workdir': bc.userconfig.get('DEFAULT', 'bee_workdir'),
    'container_runtime': bc.userconfig.get('task_manager', 'container_runtime'),
    'job_template': bc.userconfig.get('task_manager', 'job_template', fallback=None),
}
if WLS == 'Slurm':
    worker_class = SlurmWorker
    workload_args['slurm_socket'] = bc.userconfig.get('slurmrestd', 'slurm_socket')
elif WLS == 'LSF':
    worker_class = LSFWorker
elif WLS == 'Simple':
    worker_class = SimpleWorker

print(workload_args)
print()
worker = WorkerInterface(worker_class, **workload_args)

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
