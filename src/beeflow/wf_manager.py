"""Server launch script."""
import os
import sys
import logging
import signal
import configparser
import jsonpickle
import requests
import pathlib
import types
import tempfile
import shutil
import time
import tarfile
import getpass
import subprocess
import cwl_utils.parser_v1_0 as cwl
# Server and REST handlin
from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse
# Interacting with the rm, tm, and scheduler
from werkzeug.datastructures import FileStorage
# Temporary clamr parser
import beeflow.common.parser.parse_clamr as parser
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging

sys.excepthook = bee_logging.catch_exception

if len(sys.argv) > 2:
    bc = BeeConfig(userconfig=sys.argv[1])
else:
    bc = BeeConfig()


if bc.userconfig.has_section('workflow_manager'):
    # Try getting listen port from config if exists, use WM_PORT if it doesnt exist
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port)
    log.info(f"wfm_listen_port {wfm_listen_port}")
else:
    log.info("[workflow_manager] section not found in configuration file, default values\
 will be added")

    wfm_dict = {
        'listen_port': bc.default_wfm_port,
    }

    bc.modify_section('user', 'workflow_manager', wfm_dict)
    sys.exit("Please check " + str(bc.userconfig_file) + " and restart WorkflowManager")

if bc.userconfig.has_section('task_manager'):
    # Try getting listen port from config if exists, use default if it doesnt exist
    TM_LISTEN_PORT = bc.userconfig['task_manager'].get('listen_port', bc.default_tm_port)
else:
    log.info("[task_manager] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    TM_LISTEN_PORT = bc.default_tm_port

if bc.userconfig.has_section('scheduler'):
    # Try getting listen port from config if exists, use 5050 if it doesnt exist
    SCHED_LISTEN_PORT = bc.userconfig['scheduler'].get('listen_port', bc.default_sched_port)
else:
    log.info("[scheduler] section not found in configuration file, default values will be used")
    # Set Workflow manager ports, attempt to prevent collisions
    SCHED_LISTEN_PORT = bc.default_sched_port

flask_app = Flask(__name__)
api = Api(flask_app)

bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
UPLOAD_FOLDER = os.path.join(bee_workdir, 'current_workflow')
# Create the upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
try:
    wfi = WorkflowInterface(user='neo4j', bolt_port=bc.userconfig.get('graphdb', 'bolt_port'),
                            db_hostname=bc.userconfig.get('graphdb', 'hostname'),
                            password=bc.userconfig.get('graphdb', 'dbpass'))
except (KeyError, configparser.NoSectionError) as e:
    wfi = WorkflowInterface()


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


def validate_wf_id(func):
    """Validate tempoary hard coded workflow id."""
    def wrapper(*args, **kwargs):
        wf_id = kwargs['wf_id']
        current_wf_id = wfi.get_workflow_id()
        if wf_id != current_wf_id:
            log.info(f'Wrong workflow id. Set to {wf_id}, but should be {current_wf_id}')
            resp = make_response(jsonify(status='wf_id not found'), 404)
            return resp
        return func(*args, **kwargs)
    return wrapper

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
    ps = subprocess.run([f"ps aux | grep {user} | grep [n]eo4j"], shell=True, stdout=subprocess.PIPE)
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
        self.reqparse.add_argument('filename', type=FileStorage, required=False,
                                   location='files')
        self.reqparse.add_argument('workflow', type=FileStorage, required=False,
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
            for w in workflows:
                wf_path = os.path.join(workflows_dir, w) 
                status_path = os.path.join(wf_path, 'bee_wf_status')
                name_path = os.path.join(wf_path, 'bee_wf_name')
                wf_id = w
                status = pathlib.Path(status_path).read_text()
                name = pathlib.Path(name_path).read_text()
                job_list.append([name, wf_id, status])

        resp = make_response(jsonify(job_list=jsonpickle.encode(job_list)), 200)
        return resp

    def post(self):
        """Get a workflow or give file not found error."""
        data = self.reqparse.parse_args()

        if data['workflow'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp
        # Workflow file
        cwl_file = data['workflow']
        filename = data['filename'].read().decode()
        job_name = data['wf_name'].read().decode()

        if cwl_file:
            # We have to bind mount a new GDB with charliecloud.
            kill_gdb()
            # Remove the old gdb
            remove_gdb()
            # Start a new GDB 
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
            script_path = get_script_path()
            subprocess.run([f'{script_path}/start_gdb.py', '--gdb_workdir', gdb_workdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Need to wait a moment for the GDB
            time.sleep(10)

            # Save the workflow temporarily to this folder 
            temp_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
            cwl_file.save(temp_path)

            # Parse the workflow and add it to the database
            top = cwl.load_document(temp_path)
            # Remove the workflow file

            if wfi.workflow_initialized() and wfi.workflow_loaded():
                # Clear the workflow if we've already run one
                wfi.finalize_workflow()
            parser.create_workflow(top, wfi)

            # Save the workflow to the workflow_id dir
            wf_id = wfi.get_workflow_id()
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            os.makedirs(workflow_dir)
            workflow_path = os.path.join(workflow_dir, filename)
            cwl_file.save(workflow_path)

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
        filename = data['filename'].read().decode()
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

            ## Copy GDB to gdb_workdir
            archive_dir = filename.split('.')[0]
            gdb_path = os.path.join(tmp_path, archive_dir, 'gdb')
            gdb_workdir = os.path.join(bee_workdir, 'current_gdb')

            shutil.copytree(gdb_path, gdb_workdir) 

             # Launch new container with bindmounted GDB
            script_path = get_script_path()
            subprocess.run([f'{script_path}/start_gdb.py', '--gdb_workdir', gdb_workdir, '--reexecute'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(10)

            # Initialize the database connection object
            wfi.initialize_workflow(inputs=None, outputs=None, existing=True)
            # Reset the workflow state and generate a new workflow ID
            wfi.reset_workflow()
            wf_id = wfi.get_workflow_id()
            reexecute = True

            # Save the workflow to the workflow_id dir
            wf_id = wfi.get_workflow_id()
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
    resp = requests.post(_resource('tm', "submit/"), json={'tasks': tasks_json})
    if resp.status_code != 200:
        log.info(f"Submit task to TM returned bad status: {resp.status_code}")


# Submit a list of tasks to the Scheduler
def submit_tasks_scheduler(sched_tasks):
    """Submit a list of tasks to the scheduler."""
    tasks_json = jsonpickle.encode(sched_tasks)
    # The workflow name will eventually be added to the wfi workflow object
    resp = requests.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks)
    if resp.status_code != 200:
        log.info(f"Something bad happened {resp.status_code}")
    return resp.json()


def setup_scheduler():
    """Get info from the resource monitor and sends it to the scheduler."""
    # Get the info for the current server
    nodes = 32

    data = rm.get()
    log.info(data)

    resources = [
        {
            'id_': data['hostname'],
            'nodes': data['nodes']
        }
    ]

    log.info(_resource('sched', "resources/"))
    resp = requests.put(_resource('sched', "resources"), json=resources)


# Used to tell if the workflow is currently paused
# Will eventually be moved to a Workflow class
WORKFLOW_PAUSED = False
SAVED_TASK = None


# Save a task when we pause
def save_task(task):
    """Save a task."""
    global SAVED_TASK
    log.info(f"Saving {task.name}")
    SAVED_TASK = task


def resume():
    """Resume a saved task."""
    global SAVED_TASK
    if SAVED_TASK is not None:
        submit_tasks_tm(SAVED_TASK)
    # Clear out the saved task
    SAVED_TASK = None


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
    @validate_wf_id
    def post(wf_id):
        """Start job. Send tasks to the task manager."""
        # Get dependent tasks that branch off of bee_init and send to the scheduler
        wfi.execute_workflow()
        tasks = wfi.get_ready_tasks()
        # Convert to a scheduler task object
        sched_tasks = tasks_to_sched(tasks)
        # Submit all dependent tasks to the scheduler
        allocation = submit_tasks_scheduler(sched_tasks)
        # Submit tasks to TM
        submit_tasks_tm(tasks)
        resp = make_response(jsonify(msg='Started workflow', status='ok'), 200)
        wf_id = wfi.get_workflow_id()
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Running')
        return "Started Workflow"

    @staticmethod
    @validate_wf_id
    def get(wf_id):
        """Check the database for the current status of all the tasks."""
        (_, tasks) = wfi.get_workflow()
        task_status = ""
        for task in tasks:
            if task.name != "bee_init" and task.name != "bee_exit":
                task_status += f"{task.name}--{wfi.get_task_state(task)}\n"
        log.info("Returned query")
        resp = make_response(jsonify(msg=task_status, status='ok'), 200)
        return resp

    @staticmethod
    @validate_wf_id
    def delete(wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        resp = requests.delete(_resource('tm'))
        if resp.status_code != 200:
            log.info(f"Delete from task manager returned bad status: {resp.status_code}")
        wf_id = wfi.get_workflow_id()
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Cancelled')

        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    @validate_wf_id
    def patch(self, wf_id):
        """Pause or resume workflow."""
        global WORKFLOW_PAUSED
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        if option == 'pause':
            WORKFLOW_PAUSED = True
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
            return resp
        if option == 'resume':
            if WORKFLOW_PAUSED:
                WORKFLOW_PAUSED = False
                resume()
            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        log.error("Invalid option")
        resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
        return resp



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

    def put(self):
        """Update the state of a task from the task manager."""
        global reexecute 
        # Figure out how to find the task in the databse and change it's state
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']


        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)

        if 'metadata' in data:
            if data['metadata'] != None:
                metadata = jsonpickle.decode(data['metadata'])
                wfi.set_task_metadata(task, metadata)

        if job_state == "COMPLETED" or job_state == "FAILED":
            tasks = wfi.finalize_task(task)
            # TODO Replace this with Steven's pause task functions
            if WORKFLOW_PAUSED:
                # If we've paused the workflow save the task until we resume
                save_task(task)
            else:
                if wfi.workflow_completed():
                    log.info("Workflow Completed")

                    archive = bc.userconfig.get('DEFAULT','use_archive')
                    if archive and not reexecute:
                        gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
                        wf_id = wfi.get_workflow_id()
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
                    if tasks:
                        sched_tasks = tasks_to_sched(tasks)
                        submit_tasks_scheduler(sched_tasks)
                        submit_tasks_tm(tasks)


        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp


api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')

if __name__ == '__main__':
    # Setup the Scheduler
    setup_scheduler()
    log.info(f'wfm_listen_port:{wfm_listen_port}')
    bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    # Putting this off for another issue so noqa to appease the lama
    flask_app.logger.addHandler(handler) #noqa
    flask_app.run(debug=True, port=str(wfm_listen_port))

