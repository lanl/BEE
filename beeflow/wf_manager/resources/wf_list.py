import os
import jsonpickle
import shutil
import tempfile
import subprocess

from flask import make_response, jsonify
from werkzeug.datastructures import FileStorage
from flask_restful import Resource, reqparse

from beeflow.cli import log
# from beeflow.common.wf_profiler import WorkflowProfiler
from beeflow.common.parser import CwlParser

import beeflow.wf_manager.resources.wf_utils as wf_utils
import beeflow.wf_manager.common.dep_manager as dep_manager
import beeflow.wf_manager.common.wf_db as wf_db


def parse_workflow(workflow_dir, main_cwl, yaml_file, wf_name):
    parser = CwlParser()
    parse_msg = "Unable to parse workflow." \
                "Please check workflow manager."

    cwl_path = os.path.join(workflow_dir, main_cwl)
    if yaml_file is not None:
        yaml_file = yaml_file
        yaml_path = os.path.join(workflow_dir, yaml_file)
        try:
            wfi = parser.parse_workflow(cwl_path, yaml_path)
        except AttributeError:
            log.error('Unable to parse')
            resp = make_response(jsonify(msg=parse_msg, status='error'), 418)
            return resp
    else:
        try:
            wfi = parser.parse_workflow(cwl_path)
        except AttributeError:
            resp = make_response(jsonify(msg=parse_msg, status='error'), 418)
            return resp
    return wfi


def create_dep_container():
    # Create new dependency container if one does not currently exist
    try:
        dep_manager.create_image()
    except dep_manager.NoContainerRuntime:
        crt_message = "Charliecloud not installed in current environment."
        log.error(crt_message)
        resp = make_response(jsonify(msg=crt_message, status='error'), 418)
        return resp


# def initialize_wf_profiler(wf_name):
#    # Initialize the workflow profiling code
#    bee_workdir = wf_utils.get_bee_workdir()
#    fname = '{}.json'.format(wf_name)
#    profile_dir = os.path.join(bee_workdir, 'profiles')
#    os.makedirs(profile_dir, exist_ok=True)
#    output_path = os.path.join(profile_dir, fname)
#    wf_profiler = WorkflowProfiler(wf_name, output_path)


def extract_wf_temp(filename, workflow_archive):
    # Make a temp directory to store the archive
    tmp_path = tempfile.mkdtemp()
    archive_path = os.path.join(tmp_path, filename)
    workflow_archive.save(archive_path)
    # Extract to tmp directory
    subprocess.run(['tar', '-xf', archive_path, '-C', tmp_path])
    return tmp_path


class WFList(Resource):
    """Interacts with existing workflows."""

    def __init__(self):
        """Don't need to initialize anything"""
        pass

    def get(self):
        """Return list of workflows to client"""
        workflow_list = wf_db.get_workflows()
        info = []
        for wf_info in workflow_list:
            wf_id = wf_info.workflow_id
            wf_status = wf_info.status
            wf_name = wf_info.name
            info.append([wf_name, wf_id, wf_status])
        resp = make_response(jsonify(workflow_list=jsonpickle.encode(info)), 200)
        return resp

    def post(self):
        """Receive a workflow, parse it, and start up a neo4j instance for it.
           Workflow manager returns a workflow ID used for subsequent communication
        """
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('wf_name', type=str, required=True,
                               location='form')
        reqparser.add_argument('main_cwl', type=str, required=True,
                               location='form')
        reqparser.add_argument('yaml', type=str, required=False,
                               location='form')
        reqparser.add_argument('wf_filename', type=str, required=True,
                               location='form')
        reqparser.add_argument('workflow_archive', type=FileStorage, required=False,
                               location='files')
        data = reqparser.parse_args()
        wf_tarball = data['workflow_archive']
        wf_filename = data['wf_filename']
        main_cwl = data['main_cwl']
        wf_name = data['wf_name']
        # None if not sent
        yaml_file = data['yaml']

        dep_manager.kill_gdb()
        dep_manager.remove_current_run()
        create_dep_container()
        # Remove the current run directory in the bee workdir

        # Save the workflow temporarily to this folder for the parser
        # This is a temporary measure until we can get the worflow ID before a parse
        temp_dir = extract_wf_temp(wf_filename, wf_tarball)
        dep_manager.start_gdb()
        dep_manager.wait_gdb(log, 10)

        wf_path = os.path.join(temp_dir, wf_filename[:-4])
        wfi = parse_workflow(wf_path, main_cwl, yaml_file, wf_name)

        # initialize_wf_profiler(wf_name)
        # Save the workflow to the workflow_id dir in the beeflow dir
        wf_id = wfi.workflow_id
        bee_workdir = wf_utils.get_bee_workdir()
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        os.makedirs(workflow_dir)

        # Copy workflow files to later archive
        for f in os.listdir(temp_dir):
            f_path = os.path.join(temp_dir, f)
            if os.path.isfile(f_path):
                shutil.copy(f_path, workflow_dir)

        # We've parsed and added temp files to wf directory so we can chuck it
        shutil.rmtree(temp_dir, ignore_errors=True)

        wf_utils.create_wf_metadata(wf_id, wf_name)
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)
        return resp

    def put(self):
        """ReExecute a workflow"""
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('wf_name', type=str, required=True,
                               location='form')
        reqparser.add_argument('wf_filename', type=str, required=True,
                               location='form')
        reqparser.add_argument('workflow_archive', type=FileStorage, required=False,
                               location='files')

        data = reqparser.parse_args()
        workflow_archive = data['workflow_archive']
        wf_filename = data['wf_filename']
        wf_name = data['wf_name']

        dep_manager.kill_gdb()
        create_dep_container()
        # Remove the current run directory in the bee workdir
        dep_manager.remove_current_run()

        tmp_dir = extract_wf_temp(wf_filename, workflow_archive)

        archive_dir = wf_filename.split('.')[0]
        gdb_path = os.path.join(tmp_dir, archive_dir, 'gdb')
        bee_workdir = wf_utils.get_bee_workdir()
        gdb_workdir = os.path.join(bee_workdir, 'current_run')
        shutil.copytree(gdb_path, gdb_workdir)
        shutil.rmtree(tmp_dir)
        # Launch new container with bindmounted GDB
        dep_manager.start_gdb(reexecute=True)
        dep_manager.wait_gdb(log, 10)
        wfi = wf_utils.get_workflow_interface()

        # Reset the workflow state and generate a new workflow ID
        wfi.reset_workflow()
        wf_id = wfi.workflow_id

        # Save the workflow to the workflow_id dir
        wf_id = wfi.workflow_id
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        os.makedirs(workflow_dir)
        wf_utils.create_wf_metadata(wf_id, wf_name)

        # Return the wf_id and created
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)
        return resp

    def patch(self):
        """Copy workflow archive"""
        reqparser = reqparse.RequestParser()
        data = reqparser.parse_args()
        bee_workdir = wf_utils.get_bee_workdir()
        wf_id = data['wf_id']
        archive_path = os.path.join(bee_workdir, 'archives', wf_id + '.tgz')
        with open(archive_path, 'rb') as a:
            archive_file = jsonpickle.encode(a.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file,
                             archive_filename=archive_filename), 200)
        return resp
