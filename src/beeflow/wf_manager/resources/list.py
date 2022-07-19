# from beeflow.wf_manager.common.defs import *
import os
import jsonpickle
import pathlib
import time
import signal
import shutil
import getpass
import tempfile
import subprocess

from flask import make_response, jsonify
from werkzeug.datastructures import FileStorage
from flask_restful import Resource, reqparse

from beeflow.cli import log
from beeflow.start_gdb import StartGDB
from beeflow.common.gdb.neo4j_driver import Neo4JNotRunning


def get_bee_workdir():
    """Get the bee workflow directory from the configuration file"""
    return os.path.expanduser('~/.beeflow')


def get_gdb_sleeptime():
    return 10


def get_wfi():
    wfi = None
    return wfi


# def get_script_path():
#    return os.path.dirname(os.path.realpath(__file__))


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
    bee_workdir = get_bee_workdir()
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

        # self.reqparse.add_argument('wf_filename', type=FileStorage, required=False,
        #                           location='files')
        # self.reqparse.add_argument('workflow', type=FileStorage, required=False,
        #                           location='files')
        # self.reqparse.add_argument('wf_id', type=FileStorage, required=False,
        #                           location='files')
        # super(JobsList, self).__init__()
        pass

    def get(self):
        """Return list of workflows to client"""
        # For each dir in bee_workdir look at its state at .bee_state
        bee_workdir = get_bee_workdir()
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        job_list = []
        # Confirm that workflow directory exist
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
        """Receive a workflow, parse it, and start up a neo4j instance for it"""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('wf_name', type=str, required=True,
                                   location='form')
        self.reqparse.add_argument('main_cwl', type=str, required=True,
                                   location='form')
        self.reqparse.add_argument('yaml', type=str, required=False,
                                   location='form')
        self.reqparse.add_argument('wf_filename', type=str, required=True,
                                   location='form')
        self.reqparse.add_argument('workflow_archive', type=FileStorage, required=False,
                                   location='files')

        wfi = get_wfi()
        bee_workdir = get_bee_workdir()
        # --ParseArguments
        data = self.reqparse.parse_args()
        print(data['workflow_archive'])

        # Workflow file
        wf_tarball = data['workflow_archive']
        wf_filename = data['wf_filename']
        main_cwl = data['main_cwl']
        job_name = data['wf_name']
        # None if not sent
        yaml_file = data['yaml']
        """Get a workflow or give file not found error."""
        if data['workflow_archive'] == "":
            resp = make_response(jsonify(msg='No file found', status='error'), 400)
            return resp
        # TODO Check that tarball is valid

        # Start a new GDB
        # --StartNewGdb
        # gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
        # script_path = get_script_path()
        # gdb_proc = StartGDB(bc, gdb_workdir)

        # --WaitGdb
        # Need to wait a moment for the GDB
        # TODO remove this when properly moved to another function
        gdb_sleep_time = 1
        log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
        time.sleep(gdb_sleep_time)

        # --FinalizeWorkflow (REMOVED)

        # --SaveTarballAndExtract
        # Save the workflow temporarily to this folder for the parser
        temp_dir = tempfile.mkdtemp()
        temp_tarball_path = os.path.join(temp_dir, wf_filename)
        wf_tarball.save(temp_tarball_path)
        # Archive tarballs must be tgz
        subprocess.run(['tar', 'xf', f'{wf_filename}', '--strip-components', '1'], cwd=temp_dir)

        # --CheckContainerRuntime
        try:
            parser = CwlParser()
        except Neo4JNotRunning:
            container_runtime = bc.userconfig.get('task_manager', 'container_runtime')
            container_msg = "Neo4j DB is not running. Please make sure " \
                            f"{container_runtime} is installed and available."
            logging.error(container_msg)
            resp = make_response(jsonify(msg=container_msg, status='error'), 418)
            return resp
        temp_cwl_path = os.path.join(temp_dir, main_cwl)
        parse_msg = "Unable to parse workflow." \
                    "Please check workflow manager."

        # --GetYamlFile
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

        # --IntializeWorkflowProfiler
        # Initialize the workflow profiling code
        # fname = '{}.json'.format(job_name)
        # profile_dir = os.path.join(bee_workdir, 'profiles')
        # os.makedirs(profile_dir, exist_ok=True)
        # output_path = os.path.join(profile_dir, fname)
        # wf_profiler = WorkflowProfiler(job_name, output_path)

        # --SaveWorkflow
        # Save the workflow to the workflow_id dir
        wf_id = wfi.workflow_id
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        os.makedirs(workflow_dir)
        workflow_path = os.path.join(workflow_dir, wf_filename)
        wf_tarball.save(workflow_path)

        # --CopyWorkflow
        # Copy workflow files to archive
        for f in os.listdir(temp_dir):
            f_path = os.path.join(temp_dir, f)
            if os.path.isfile(f_path):
                shutil.copy(f_path, workflow_dir)

        # --CreateWorkflowStatusFile
        # Create status file
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Pending')

        # --CreateWorkflowNameFile
        # Create wf name file
        name_path = os.path.join(workflow_dir, 'bee_wf_name')
        with open(name_path, 'w') as name:
            name.write(job_name)
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok', wf_id=wf_id), 201)
        return resp

    def put(self):
        """ReExecute a workflow"""
        bee_workdir = get_bee_workdir()
        wfi = get_wfi()
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
            #script_path = get_script_path()
            StartGDB(bc, gdb_workdir)
            gdb_sleep_time = get_gdb_sleeptime()
            log.info('waiting {}s for GDB to come up'.format(gdb_sleep_time))
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
        bee_workdir = get_bee_workdir()
        data = self.reqparse.parse_args()
        wf_id = data['wf_id'].read().decode()
        archive_path = os.path.join(bee_workdir, 'archives', wf_id + '.tgz')
        with open(archive_path, 'rb') as a:
            archive_file = jsonpickle.encode(a.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file,
                             archive_filename=archive_filename), 200)
        return resp
