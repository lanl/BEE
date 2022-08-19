"""Server launch script."""
import os
import sys
import logging
import signal
import jsonpickle
import json
import requests
import pathlib
import tempfile
import shutil
import time
import getpass
import subprocess

from beeflow.common.config_driver import BeeConfig as bc

# The bc object must be created before importing other parts of BEE
if len(sys.argv) > 2:
    bc.init(userconfig=sys.argv[1])
else:
    bc.init()

# Server and REST handlin
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse
# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage
# Temporary clamr parser
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.parser import CwlParser 
from beeflow.common.wf_profiler import WorkflowProfiler
from beeflow.start_gdb import StartGDB
from beeflow.cli import log
import beeflow.common.log as bee_logging

from beeflow.common.gdb.neo4j_driver import Neo4JNotRunning

sys.excepthook = bee_logging.catch_exception


wfm_listen_port = bc.get('workflow_manager', 'listen_port')
TM_LISTEN_PORT = bc.get('task_manager', 'listen_port')
SCHED_LISTEN_PORT = bc.get('scheduler', 'listen_port')

flask_app = Flask(__name__)
api = Api(flask_app)

bee_workdir = bc.get('DEFAULT','bee_workdir')
UPLOAD_FOLDER = os.path.join(bee_workdir, 'current_workflow')
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# gdb sleep time
gdb_sleep_time = bc.get('graphdb', 'sleep_time')

flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

reexecute = False


def get_script_path():
    return os.path.dirname(os.path.realpath(__file__))


def tm_url():
    """Get Task Manager url."""
    task_manager = "bee_tm/v1/task/"
    return f'http://127.0.0.1:{TM_LISTEN_PORT}/{task_manager}'


def sched_url():
    """Get Scheduler url."""
    scheduler = "bee_sched/v1/"
    return f'http://127.0.0.1:{SCHED_LISTEN_PORT}/{scheduler}'


def _resource(component, tag=""):
    """Access Task Manager or Scheduler."""
    if component == "tm":
        url = tm_url() + str(tag)
    elif component == "sched":
        url = sched_url() + str(tag)
    return url


# Instantiate the workflow interface
wfi = None
# Instantiate the workflow profiler
wf_profiler = None


class ResourceMonitor():
    """Class def to interact with resource monitor."""

    def __init__(self):
        """Construct resource monitor."""
        self.hostname = os.uname()[1].split('.')[0]
        self.nodes = 32

    def get(self):
        """Construct data dictionary for resource monitor."""
        data = {
            'hostname': self.hostname,
            'nodes': self.nodes
        }

        return data


rm = ResourceMonitor()


def process_running(pid):
    """Check if the process with pid is running"""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def kill_process(pid):
    """Kill the process with pid"""
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        log.info('Process already killed')


def kill_gdb():
    """Kill the current GDB process."""
    # TODO TERRIBLE Kludge until we can figure out a better way to get the PID
    user = getpass.getuser()
    ps = subprocess.run([f"ps aux | grep {user} | grep [n]eo4j"], shell=True,
                        stdout=subprocess.PIPE)
    if ps.stdout.decode() != '':
        gdb_pid = int(ps.stdout.decode().split()[1])
        kill_process(gdb_pid)


def remove_gdb():
    """Remove the current GDB bind mount directory"""
    gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
    old_gdb_workdir = os.path.join(bee_workdir, 'old_gdb')
    if os.path.isdir(gdb_workdir):
        # Rename the directory to guard against NFS errors
        shutil.move(gdb_workdir, old_gdb_workdir)
        time.sleep(2)
        shutil.rmtree(old_gdb_workdir)
        time.sleep(2)


# Client registers with the workflow manager.
# Workflow manager returns a workflow ID used for subsequent communication
class JobsList(Resource):
    """Class def to interact with workflow job listing."""

    def __init__(self):
        """Initialize job list class."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('wf_name', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('wf_filename', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('workflow', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('yaml', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('main_cwl', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('workflow_archive', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('wf_id', type=FileStorage, required=False,
                                   location='files')
        super(JobsList, self).__init__()

    def get(self):
        """Return list of workflows to client"""
        # For each dir in bee_workdir look at its state at .bee_state
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        job_list = []
        if os.path.isdir(workflows_dir):
            workflows = next(os.walk(workflows_dir))[1]
            for wf_id in workflows:
                wf_path = os.path.join(workflows_dir, wf_id)
                status_path = os.path.join(wf_path, 'bee_wf_status')
                name_path = os.path.join(wf_path, 'bee_wf_name')
                status = pathlib.Path(status_path).read_text()
                name = pathlib.Path(name_path).read_text()
                job_list.append([name, wf_id, status])

        resp = make_response(jsonify(job_list=jsonpickle.encode(job_list)), 200)
        return resp

    # TODO PyLama pointed out this function is too complex it should be broken up
    def post(self):  # NOQA
        global wfi
        global wf_profiler
        """Get a workflow or give file not found error."""
        data = self.reqparse.parse_args()

        if data['workflow'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp
        # Workflow file
        wf_tarball = data['workflow']
        wf_filename = data['wf_filename'].read().decode()
        main_cwl = data['main_cwl'].read().decode()
        job_name = data['wf_name'].read().decode()
        # None if not sent
        yaml_file = data['yaml']

        if wf_tarball:
            # We have to bind mount a new GDB with charliecloud.
            kill_gdb()
            # Remove the old gdb
            remove_gdb()
            # Start a new GDB
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
            script_path = get_script_path()
            gdb_proc = StartGDB(bc, gdb_workdir)
            # Need to wait a moment for the GDB
            log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
            time.sleep(gdb_sleep_time)

            if wfi:
                if wfi.workflow_initialized() and wfi.workflow_loaded():
                    # Clear the workflow if we've already run one
                    wfi.finalize_workflow()

            # Save the workflow temporarily to this folder for the parser

            temp_dir = tempfile.mkdtemp()
            temp_tarball_path = os.path.join(temp_dir, wf_filename)
            wf_tarball.save(temp_tarball_path)
            # Archive tarballs must be tgz
            subprocess.run(['tar', 'xf', f'{wf_filename}', '--strip-components', '1'], cwd=temp_dir)

            try:
                parser = CwlParser()
            except Neo4JNotRunning:
                container_runtime = bc.get('task_manager', 'container_runtime')
                container_msg = "Neo4j DB is not running. Please make sure " \
                                f"{container_runtime} is installed and available."
                logging.error(container_msg)
                resp = make_response(jsonify(msg=container_msg, status='error'), 418)
                return resp
            temp_cwl_path = os.path.join(temp_dir, main_cwl)
            parse_msg = "Unable to parse workflow." \
                        "Please check workflow manager."
            if yaml_file is not None:
                yaml_file = yaml_file.read().decode()
                temp_yaml_path = os.path.join(temp_dir, yaml_file)
                try:
                    wfi = parser.parse_workflow(temp_cwl_path, temp_yaml_path)
                except AttributeError:
                    log.error('Unable to parse')
                    resp = make_response(jsonify(msg=parse_msg, status='error'), 418)
                    return resp
            else:
                try:
                    wfi = parser.parse_workflow(temp_cwl_path)
                except AttributeError:
                    resp = make_response(jsonify(msg=parse_msg, status='error'), 418)
                    return resp

            # Initialize the workflow profiling code
            fname = f'{job_name}.json'
            profile_dir = os.path.join(bee_workdir, 'profiles')
            os.makedirs(profile_dir, exist_ok=True)
            output_path = os.path.join(profile_dir, fname)
            wf_profiler = WorkflowProfiler(job_name, output_path)

            # Save the workflow to the workflow_id dir
            wf_id = wfi.workflow_id
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            os.makedirs(workflow_dir)
            # workflow_path = os.path.join(workflow_dir, wf_filename)
            # wf_tarball.save(workflow_path)

            # Copy workflow files to archive
            for f in os.listdir(temp_dir):
                f_path = os.path.join(temp_dir, f)
                if os.path.isfile(f_path):
                    shutil.copy(f_path, workflow_dir)

            # Create status file
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'w') as status:
                status.write('Pending')

            # Create wf name file
            name_path = os.path.join(workflow_dir, 'bee_wf_name')
            with open(name_path, 'w') as name:
                name.write(job_name)
            resp = make_response(jsonify(msg='Workflow uploaded', status='ok', wf_id=wf_id), 201)
            return resp
        else:
            resp = make_response(jsonify(msg='File corrupted', status='error'), 400)
            return resp

    def put(self):
        """ReExecute a workflow"""
        global reeexecute
        data = self.reqparse.parse_args()
        if data['workflow_archive'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp

        workflow_archive = data['workflow_archive']
        filename = data['wf_filename'].read().decode()
        job_name = data['wf_name'].read().decode()

        if workflow_archive:
            # Make a temp directory to store the archive
            tmp_path = tempfile.mkdtemp()
            archive_path = os.path.join(tmp_path, filename)
            workflow_archive.save(archive_path)
            # Extract to tmp directory
            subprocess.run(['tar', '-xf', archive_path, '-C', tmp_path])

            # Kill existing GDB if needed
            kill_gdb()
            remove_gdb()

            # Copy GDB to gdb_workdir
            archive_dir = filename.split('.')[0]
            gdb_path = os.path.join(tmp_path, archive_dir, 'gdb')
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')

            shutil.copytree(gdb_path, gdb_workdir)

            # Launch new container with bindmounted GDB
            script_path = get_script_path()
            gdb_proc = StartGDB(bc, gdb_workdir, reexecute=True)
            log.info(f'waiting {gdb_sleep_time}s for GDB to come up')
            time.sleep(gdb_sleep_time)

            # Initialize the database connection object
            wfi.initialize_workflow(inputs=None, outputs=None, existing=True)
            # Reset the workflow state and generate a new workflow ID
            wfi.reset_workflow()
            wf_id = wfi.workflow_id

            # Save the workflow to the workflow_id dir
            wf_id = wfi.workflow_id
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            os.makedirs(workflow_dir)

            # Create status file
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'w') as status:
                status.write('Pending')

            # Create wf name file
            name_path = os.path.join(workflow_dir, 'bee_wf_name')
            with open(name_path, 'w') as name:
                name.write(job_name)

            # Return the wf_id and created
            resp = make_response(jsonify(wf_id=wf_id), 201)
            return resp

    def patch(self):
        """Copy workflow archive"""
        data = self.reqparse.parse_args()
        wf_id = data['wf_id'].read().decode()
        archive_path = os.path.join(bee_workdir, 'archives', wf_id + '.tgz')
        with open(archive_path, 'rb') as a:
            archive_file = jsonpickle.encode(a.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file,
                             archive_filename=archive_filename), 200)
        return resp


# Submit tasks to the TM
def submit_tasks_tm(tasks):
    """Submit a task to the task manager."""
    # Serialize task with json
    tasks_json = jsonpickle.encode(tasks)
    # Send task_msg to task manager
    names = [task.name for task in tasks]
    log.info(f"Submitted {names} to Task Manager")
    try:
        resp = requests.post(_resource('tm', "submit/"), json={'tasks': tasks_json})
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to task manager to submit tasks.')
        return

    if resp.status_code != 200:
        log.info(f"Submit task to TM returned bad status: {resp.status_code}")


# Submit a list of tasks to the Scheduler
def submit_tasks_scheduler(sched_tasks):
    """Submit a list of tasks to the scheduler."""
    # The workflow name will eventually be added to the wfi workflow object
    try:
        resp = requests.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to scheduler to submit tasks.')
        return

    if resp.status_code != 200:
        log.info(f"The BEE scheduler failed on submission with error: {resp.status_code}")
    return resp.json()


def setup_scheduler():
    """Get info from the resource monitor and sends it to the scheduler."""
    # Get the info for the current server
    data = rm.get()

    resources = [
        {
            'id_': data['hostname'],
            'nodes': data['nodes']
        }
    ]

    log.info(_resource('sched', "resources/"))

    try:
        resp = requests.put(_resource('sched', "resources"), json=resources)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to scheduler. Using FIFO scheduling.')
    if resp != requests.codes.okay:
        log.info('Scheduler setup did not work')


def tasks_to_sched(tasks):
    """Convert gdb tasks to sched tasks."""
    sched_tasks = []
    for task in tasks:
        sched_task = {
            'workflow_name': 'workflow',
            'task_name': task.name,
            'requirements': {
                'max_runtime': 1,
                'nodes': 1
            }
        }
        sched_tasks.append(sched_task)
    return sched_tasks


# This class is where we act on existing jobs
class JobActions(Resource):
    """Class to handle job actions."""

    def __init__(self):
        """Initialize JobActions class with passed json object."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    @staticmethod
    def post(wf_id):
        """Start workflow. Send ready tasks to the task manager."""
        state = wfi.get_workflow_state()
        if state == 'RUNNING' or state == 'PAUSED' or state == 'COMPLETED':
            resp = make_response(jsonify(msg='Cannot start workflow it is currently '
                                        f'{state.capitalize()}', 
                                            status='ok'), 200)
            return resp
        wfi.execute_workflow()
        tasks = wfi.get_ready_tasks()
        # Convert to a scheduler task object
        sched_tasks = tasks_to_sched(tasks)
        # Submit all dependent tasks to the scheduler
        allocation = submit_tasks_scheduler(sched_tasks)  # NOQA

        # Submit tasks to TM
        submit_tasks_tm(tasks)
        wf_id = wfi.workflow_id
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Running')

        resp = make_response(jsonify(msg='Started workflow!', status='ok'), 200)
        return resp

    @staticmethod
    def get(wf_id):
        """Check the database for the current status of all the tasks."""
        if wfi is not None:
            (_, tasks) = wfi.get_workflow()
            tasks_status = ""
            for task in tasks:
                tasks_status += f"{task.name}--{wfi.get_task_state(task)}"
                if task != tasks[len(tasks) - 1]:
                    tasks_status += '\n'
            log.info("Returned query")
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'r') as status:
                wf_status = status.readline()
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='ok'), 200)
        else:
            log.info(f"Bad query for wf {wf_id}.")
            wf_status = 'No workflow with that ID is currently loaded'
            tasks_status = 'Unavailable'
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='not found'), 404)
        return resp

    @staticmethod
    def delete(wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        try:
            resp = requests.delete(_resource('tm'))
        except requests.exceptions.ConnectionError:
            log.error('Unable to connect to task manager to delete.')
            resp = make_response(jsonify(status='Could not cancel'), 404)
            return
        if resp.status_code != 200:
            log.info(f"Delete from task manager returned bad status: {resp.status_code}")
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        status_path = os.path.join(workflows_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Cancelled')

        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        workflow_state = wfi.get_workflow_state()
        if workflow_state == 'PAUSED' and option == 'pause':
            resp_msg = 'Workflow already paused'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'RUNNING' and option == 'resume':
            resp_msg = 'Workflow already running'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'SUBMITTED':
            if option == 'pause':
                resp_msg = 'Workflow has not been started yet. Cannot Pause.'
            elif option == 'resume':
                resp_msg = 'Workflow has not been started yet. Cannot Resume.'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'COMPLETED':
            log.info('Workflow Completed. Cannot Pause.')
            resp = make_response(jsonify(status='Can only pause running workflows'), 200)
            return resp

        if option == 'pause':
            wfi.pause_workflow()
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
        elif option == 'resume':
            wfi.resume_workflow()
            tasks = wfi.get_ready_tasks()
            sched_tasks = tasks_to_sched(tasks)
            submit_tasks_scheduler(sched_tasks)
            submit_tasks_tm(tasks)

            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        else:
            resp = make_response(jsonify(status='Pause/Resume recieved invalid option'), 200)
            log.error("Invalid option")
            resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
            return resp


archive = bc.get('DEFAULT','use_archive')

class JobUpdate(Resource):
    """Class to interact with an existing job."""

    def __init__(self):
        """Initialize JobUpdate with task_id and job_state requirements."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task_id', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('metadata', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('task_info', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('output', location='json', required=False)

    def put(self):
        """Update the state of a task from the task manager."""
        global reexecute
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']
        task_info = data['task_info']

        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)
        wf_profiler.add_state_change(task, job_state)

        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                wfi.set_task_metadata(task, metadata)

        # Get output from the task
        if 'output' in data and data['output'] is not None:
            fname = f'{wfi.workflow_id}_{task.id}_{int(time.time())}.json'
            task_output_path = os.path.join(bee_workdir, fname)
            with open(task_output_path, 'w') as fp:
                json.dump(json.loads(data['output']), fp, indent=4)

        if job_state == "COMPLETED":
            for output in task.outputs:
                if output.glob != None:
                    wfi.set_task_output(task, output.id, output.glob)
                else:
                    wfi.set_task_output(task, output.id, "temp")

            if wfi.workflow_completed():
                log.info("Workflow Completed")

                workflows_dir = os.path.join(bee_workdir, 'workflows')
                wf_id = wfi.workflow_id
                workflow_dir = os.path.join(workflows_dir, wf_id)
                status_path = os.path.join(workflow_dir, 'bee_wf_status')
                with open(status_path, 'w') as status:
                    status.write('Completed')
                wfi.workflow_completed()


                # Save the profile
                wf_profiler.save()
                if archive and not reexecute:
                    gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
                    wf_id = wfi.workflow_id
                    workflows_dir = os.path.join(bee_workdir, 'workflows')
                    workflow_dir = os.path.join(workflows_dir, wf_id)
                    # Archive GDB
                    shutil.copytree(gdb_workdir, workflow_dir + '/gdb')
                    # Archive Config
                    shutil.copyfile(os.path.expanduser("~") + '/.config/beeflow/bee.conf',
                            workflow_dir + '/' + 'bee.conf')
                    status_path = os.path.join(workflow_dir, 'bee_wf_status')
                    with open(status_path, 'w') as status:
                        status.write('Archived')
                    archive_dir = os.path.join(bee_workdir, 'archives')
                    os.makedirs(archive_dir, exist_ok=True)
                    #archive_path = os.path.join(archive_dir, wf_id + '_archive.tgz')
                    archive_path = f'../archives/{wf_id}.tgz'
                    # We use tar directly since tarfile is apparently very slow
                    subprocess.call(['tar', '-czf', archive_path, wf_id], cwd=workflows_dir)
                else:
                    reexecute = False
            else:
                tasks = wfi.finalize_task(task)
                if wfi.get_workflow_state() != 'PAUSED':
                    if tasks:
                        sched_tasks = tasks_to_sched(tasks)
                        submit_tasks_scheduler(sched_tasks)
                        submit_tasks_tm(tasks)

        elif job_state == "FAILED" or job_state == "TIMEOUT":
            if 'task_info' in data and data['task_info'] is not None:
                task_info = jsonpickle.decode(data['task_info'])
                checkpoint_file = task_info['checkpoint_file']
                new_task = wfi.restart_task(task, checkpoint_file)
                if new_task is None:                    
                    log.info("No more restarts")
                    #state = wfi.get_task_state(task)
                    #wfi.set_task_state(task, f"RESTART FAILED: {state}")
                    #wfi.set_task_state(task, job_state)
                    state = wfi.get_task_state(task)
                    resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
                    return resp
                else:                               
                    submit_tasks_tm([new_task])       
            else:
                log.info("TM didn't send task info for failed task")
                resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
                return resp

        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp


@flask_app.route('/bee_wfm/v1/status/<string:wf_id>')
def status(wf_id):
    """Report various workflow status info and metrics."""
    wf = {
        'complete': wfi.workflow_completed(),
    }
    return make_response(jsonify(**wf), 200)


api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')

if __name__ == '__main__':
    # Setup the Scheduler
    setup_scheduler()
    log.info(f'wfm_listen_port:{wfm_listen_port}')
    bee_workdir = bc.get('DEFAULT','bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    # Putting this off for another issue so noqa to appease the lama
    flask_app.logger.addHandler(handler) #noqa
    flask_app.run(debug=False, port=str(wfm_listen_port))

