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
tm_name = bc.userconfig['task_manager'].get('name', 'local_tm')

# Check Workflow manager port, use default if none.
if bc.userconfig.has_section('workflow_manager'):
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',
                                                            bc.default_wfm_port)
else:
    wfm_listen_port = bc.default_wfm_port

flask_app = Flask(__name__)
api = Api(flask_app)

presubmit_queue = [] # Code to be run before submission
submit_queue = []  # tasks ready to be submitted
job_queue = []  # jobs that are being monitored
completion_queue = [] # Code to be run after job completion


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


def write_request_file(fname, resp):
    """Write a request to a file."""
    # Write the file (this iterates over the content to handle large files)
    with open(fname, 'wb') as fp:
        for chunk in resp.iter_content(chunk_size=8192):
            fp.write(chunk)


def pull_file(fname):
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
            write_request_file(tarfile, resp)
            subprocess.run(['tar', '-xvf', tarfile])
        else:
            write_request_file(fname, resp)
    except requests.exceptions.ConnectionError:
        log.error('Could not connect to the WFM to pull file {}'.format(fname))


def presubmit_jobs():
    """Run job code that needs be done before submission."""
    while presubmit_queue:
        task_data = presubmit_queue.pop(0)
        task = task_data['task']
        extra_requirements = task_data['extra_requirements']
        # TODO: Check for extra requirements
        log.info('Running presubmit code for task {}'.format(task.name))
        # submit_queue
        cwd = os.getcwd()
        if 'pull' in extra_requirements and 'workdir' in extra_requirements:
            workdir = extra_requirements['workdir']
            pull_files = extra_requirements['pull']
            # Change to the current working directory of tasks
            os.chdir(workdir)
            for file_ in pull_files:
                log.info('Pulling file {} from the WFM'.format(file_))
                pull_file(file_)
            os.chdir(cwd)
        # Now see if we need to pull any containers (this will need to be hamdled by the Builder at some point)
        for hint in task.hints:
            if hint.req_class == 'DockerRequirement' and hint.key == 'dockerImageId':
                # Check if the container exists
                if not os.path.exists(hint.value):
                    log.info("Container file %s doesn't exists on this system, trying to pull it"
                             % (hint.value,))
                    # If the container doesn't exist, then try to pull it from the WFM
                    basename = os.path.basename(hint.value)
                    try:
                        resp = requests.get(f'{_wfm()}/bee_wfm/v1/files/{basename}')
                        if not resp.ok:
                            log.error('Could not pull container {} from the WFM'.format(hint.value))
                            continue
                        write_request_file(hint.value, resp)
                    except requests.exceptions.ConnectionError:
                        log.error('Could not connect to the WFM')
        # Now add it to the submit queue
        submit_queue.append({task.id: task, 'extra_requirements': extra_requirements})


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    while len(submit_queue) >= 1:
        # Single value dictionary
        task_dict = submit_queue.pop(0)
        task = next(iter(task_dict.values()))
        extra_requirements = task_dict['extra_requirements']
        try:
            job_id, job_state = worker.submit_task(task)
            log.info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
            # place job in queue to monitor
            job_queue.append({
                'task': task,
                'job_id': job_id,
                'job_state': job_state,
                'extra_requirements': extra_requirements,
            })
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


def send_file_or_dir(fname):
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


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    for job in job_queue[:]:
        task = job['task']
        job_id = job['job_id']
        job_state = worker.query_task(job_id)


        extra_requirements = job['extra_requirements']
        log.info('Job has extra requirements {}'.format(extra_requirements))
        if job_state == 'COMPLETED':
            # TODO: Run any completion code here
            if 'push' in extra_requirements:
                # Push files back the WFM
                push_files = extra_requirements['push']
                log.info('Pusing files {}'.format(','.join(push_files)))
                for fname in push_files:
                    # This checks multiple locations for output files, since
                    # stdout results may have been in the cwd of the TM
                    try:
                        # Check for files in the workdir and in the CWD
                        workdir_name = os.path.join(extra_requirements['workdir'], fname)
                        cwd_name = os.path.join(os.getcwd(), fname)
                        if os.path.exists(workdir_name):
                            send_file_or_dir(workdir_name)
                        elif os.path.exists(cwd_name):
                            send_file_or_dir(cwd_name)
                        else:
                            log.info('File {} could not be found'.format(fname))
                    except requests.exceptions.ConnectionError:
                        log.error('Could not connect to the WFM')


        if job_state != job['job_state']:
            log.info(f'{task.name} {job["job_state"]} -> {job_state}')
            job['job_state'] = job_state
            update_task_state(task.id, job_state)

        if job_state in ('FAILED', 'COMPLETED', 'CANCELLED', 'ZOMBIE'):
            # TODO: Maybe removal should be done outside of the loop
            # Remove from the job queue. Our job is finished
            job_queue.remove(job)
            # Add it to the completion queue
            completion_queue.append(job)
            log.info(f'Job {job_id} done {task.name}: removed from job status queue')


def complete_jobs():
    """This runs code that needs to be run on job completion."""
    while completion_queue:
        job = completion_queue.pop(0)
        task = job['task']
        extra_requirements = job['extra_requirements']
        log.info('Running completion code for task {}'.format(task.name))
        """
        if job['job_state'] == 'COMPLETED':
            # TODO: Run any completion code here
            if 'push' in extra_requirements:
                # Push files back the WFM
                push_files = extra_requirements['push']
                for fname in push_files:
                    # This checks multiple locations for output files, since
                    # stdout results may have been in the cwd of the TM
                    try:
                        # Check for files in the workdir and in the CWD
                        workdir_name = os.path.join(extra_requirements['workdir'], fname)
                        cwd_name = os.path.join(os.getcwd(), fname)
                        if os.path.exists(workdir_name):
                            send_file_or_dir(workdir_name)
                        elif os.path.exists(cwd_name):
                            send_file_or_dir(cwd_name)
                        else:
                            log.info('File {} could not be found'.format(fname))
                    except requests.exceptions.ConnectionError:
                        log.error('Could not connect to the WFM')

        """

def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    presubmit_jobs()
    submit_jobs()
    update_jobs()
    complete_jobs()


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
            'tm_name': tm_name,
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
        self.reqparse.add_argument('extra_requirements', type=str, location='json')

    def post(self):
        """Receives task from WFM."""
        data = self.reqparse.parse_args()
        tasks = jsonpickle.decode(data['tasks'])
        extra_requirements = jsonpickle.decode(data['extra_requirements'])
        for task in tasks:
            # submit_queue.append({task.id: task, 'extra_requirements': extra_requirements})
            # log.info(f"Added {task.name} task to the submit queue")
            presubmit_queue.append({'task': task,
                                    'extra_requirements': extra_requirements[task.id]})
            log.info(f"Added {task.name} task to the pre-submission queue")
            log.info('Task {} has extra requirements: {}'.format(task.name, extra_requirements))
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
