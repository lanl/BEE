"""The workflow list module.

This contains endpoints forsubmitting, starting, and reexecuting workflows.
"""

import os
import subprocess
import traceback
import jsonpickle

from flask import make_response, jsonify
from werkzeug.datastructures import FileStorage
from flask_restful import Resource, reqparse

from beeflow.common import log as bee_logging
# from beeflow.common.wf_profiler import WorkflowProfiler
from beeflow.common.parser import CwlParser, CwlParseError

from beeflow.wf_manager.resources import wf_utils
from beeflow.wf_manager.common import dep_manager
from beeflow.wf_manager.common import wf_db
from beeflow.common import wf_data

log = bee_logging.setup(__name__)


def parse_workflow(wfi, wf_id, workflow_dir, main_cwl, yaml_file):
    """Run the parser."""
    parser = CwlParser(wfi)
    cwl_path = os.path.join(workflow_dir, main_cwl)
    if yaml_file is not None:
        yaml_path = os.path.join(workflow_dir, yaml_file)
        parser.parse_workflow(wf_id, cwl_path, yaml_path)
    else:
        parser.parse_workflow(wf_id, cwl_path)


# def initialize_wf_profiler(wf_name):
#    # Initialize the workflow profiling code
#    bee_workdir = wf_utils.get_bee_workdir()
#    fname = '{}.json'.format(wf_name)
#    profile_dir = os.path.join(bee_workdir, 'profiles')
#    os.makedirs(profile_dir, exist_ok=True)
#    output_path = os.path.join(profile_dir, fname)
#    wf_profiler = WorkflowProfiler(wf_name, output_path)


def extract_wf(wf_id, filename, workflow_archive, reexecute=False):
    """Extract a workflow into the workflow directory."""
    wf_utils.create_workflow_dir(wf_id)
    wf_dir = wf_utils.get_workflow_dir(wf_id)
    archive_path = os.path.join(wf_dir, filename)
    workflow_archive.save(archive_path)
    if not reexecute:
        subprocess.run(['tar', '-xf', archive_path, '-C', wf_dir], check=False)
        cwl_dir = os.path.join(wf_dir, filename.split('.')[0])
        return cwl_dir

    subprocess.run(['tar', '-xf', archive_path, '--strip-components=1',
                    '-C', wf_dir], check=False)
    archive_dir = os.path.join(wf_dir, 'gdb')
    return archive_dir


class WFList(Resource):
    """Interacts with existing workflows."""

    def get(self):
        """Return list of workflows to client."""
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
        """Receive a workflow, parse it, and start up a neo4j instance for it."""
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('wf_name', type=str, required=True,
                               location='form')
        reqparser.add_argument('main_cwl', type=str, required=True,
                               location='form')
        reqparser.add_argument('yaml', type=str, required=False,
                               location='form')
        reqparser.add_argument('wf_filename', type=str, required=True,
                               location='form')
        reqparser.add_argument('workdir', type=str, required=True,
                               location='form')
        reqparser.add_argument('workflow_archive', type=FileStorage, required=False,
                               location='files')
        data = reqparser.parse_args()
        wf_tarball = data['workflow_archive']
        wf_filename = data['wf_filename']
        main_cwl = data['main_cwl']
        wf_name = data['wf_name']
        wf_workdir = data['workdir']
        # None if not sent
        yaml_file = data['yaml']

        try:
            dep_manager.create_image()
        except dep_manager.NoContainerRuntime:
            crt_message = "Charliecloud not installed in current environment."
            log.error(crt_message)
            resp = make_response(jsonify(msg=crt_message, status='error'), 418)
            return resp

        wf_id = wf_data.generate_workflow_id()
        wf_dir = extract_wf(wf_id, wf_filename, wf_tarball)
        bolt_port = wf_utils.get_open_port()
        http_port = wf_utils.get_open_port()
        https_port = wf_utils.get_open_port()
        gdb_pid = dep_manager.start_gdb(wf_dir, bolt_port, http_port, https_port)
        wf_db.add_workflow(wf_id, wf_name, 'Pending', wf_dir, bolt_port, gdb_pid)
        dep_manager.wait_gdb(log)

        try:
            # wfi = parse_workflow(wf_path, main_cwl, yaml_file)
            wfi = wf_utils.get_workflow_interface(wf_id)
            parse_workflow(wfi, wf_id, wf_dir, main_cwl, yaml_file)
        except CwlParseError as err:
            traceback.print_exc()
            log.error('Failed to parse file')
            return make_response(jsonify(msg=f'Parser: {err.args[0]}', status='error'), 400)
        # initialize_wf_profiler(wf_name)

        wf_utils.create_wf_metadata(wf_id, wf_name)
        _, tasks = wfi.get_workflow()
        for task in tasks:
            metadata = wfi.get_task_metadata(task)
            metadata['workdir'] = wf_workdir
            wfi.set_task_metadata(task, metadata)
            wf_db.add_task(task.id, wf_id, task.name, "WAITING")
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)
        return resp

    def put(self):
        """Reexecute a workflow."""
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('wf_name', type=str, required=True,
                               location='form')
        reqparser.add_argument('wf_filename', type=str, required=True,
                               location='form')
        reqparser.add_argument('workdir', type=str, required=True,
                               location='form')
        reqparser.add_argument('workflow_archive', type=FileStorage, required=False,
                               location='files')
        data = reqparser.parse_args()
        workflow_archive = data['workflow_archive']
        wf_filename = data['wf_filename']
        wf_name = data['wf_name']
        wf_workdir = data['workdir']

        try:
            dep_manager.create_image()
        except dep_manager.NoContainerRuntime:
            crt_message = "Charliecloud not installed in current environment."
            log.error(crt_message)
            resp = make_response(jsonify(msg=crt_message, status='error'), 418)
            return resp

        wf_id = wf_data.generate_workflow_id()
        wf_dir = extract_wf(wf_id, wf_filename, workflow_archive, reexecute=True)
        bolt_port = wf_utils.get_open_port()
        http_port = wf_utils.get_open_port()
        https_port = wf_utils.get_open_port()
        gdb_pid = dep_manager.start_gdb(wf_dir, bolt_port, http_port,
                                        https_port, reexecute=True)
        wf_db.add_workflow(wf_id, wf_name, 'Pending', wf_dir, bolt_port, gdb_pid)
        dep_manager.wait_gdb(log)
        wfi = wf_utils.get_workflow_interface(wf_id)
        wfi.reset_workflow(wf_id)
        wf_utils.create_wf_metadata(wf_id, wf_name)

        _, tasks = wfi.get_workflow()
        for task in tasks:
            metadata = wfi.get_task_metadata(task)
            metadata['workdir'] = wf_workdir
            wfi.set_task_metadata(task, metadata)
        # Return the wf_id and created
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)
        return resp

    def patch(self):
        """Copy workflow archive."""
        reqparser = reqparse.RequestParser()
        data = reqparser.parse_args()
        bee_workdir = wf_utils.get_bee_workdir()
        wf_id = data['wf_id']
        archive_path = os.path.join(bee_workdir, 'archives', wf_id + '.tgz')
        with open(archive_path, 'rb') as archive:
            archive_file = jsonpickle.encode(archive.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file,
                             archive_filename=archive_filename), 200)
        return resp
