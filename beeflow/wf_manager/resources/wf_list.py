"""The workflow list module.

This contains endpoints forsubmitting, starting, and reexecuting workflows.
"""

import os
import subprocess
import jsonpickle

from flask import make_response, jsonify
from werkzeug.datastructures import FileStorage
from flask_restful import Resource, reqparse
from celery import shared_task  # noqa (pylama can't find celery imports)

from beeflow.common import log as bee_logging
# from beeflow.common.wf_profiler import WorkflowProfiler

from beeflow.wf_manager.resources import wf_utils
from beeflow.wf_manager.common import dep_manager
from beeflow.common import wf_data

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db

log = bee_logging.setup(__name__)


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
    cwl_dir = wf_dir + "/bee_workflow"
    if not reexecute:
        os.mkdir(cwl_dir)
        subprocess.run(['tar', '-xf', archive_path, '-C', cwl_dir], check=False)
        return cwl_dir

    os.mkdir(cwl_dir)
    subprocess.run(['tar', '-xf', archive_path, '--strip-components=1',
                    '-C', wf_dir], check=False)
    return cwl_dir


@shared_task(ignore_result=True)
def init_workflow(wf_id, wf_name, wf_dir, wf_workdir, bolt_port, http_port,
                  https_port, no_start, workflow=None, tasks=None, reexecute=False):
    """Initialize the workflow in a separate process."""
    print('Initializing GDB and workflow...')
    try:
        dep_manager.create_image()
    except dep_manager.NoContainerRuntime:
        crt_message = "Charliecloud not installed in current environment."
        log.error(crt_message)
        return

    gdb_pid = dep_manager.start_gdb(wf_dir, bolt_port, http_port, https_port, reexecute=reexecute)
    dep_manager.wait_gdb(log)

    wfi = wf_utils.get_workflow_interface_by_bolt_port(wf_id, bolt_port)
    if reexecute:
        wfi.reset_workflow(wf_id)
    else:
        wfi.initialize_workflow(workflow)

    # initialize_wf_profiler(wf_name)

    log.info('Setting workflow metadata')
    wf_utils.create_wf_metadata(wf_id, wf_name)
    db = connect_db(wfm_db, db_path)
    if reexecute:
        _, tasks = wfi.get_workflow()
        # Tasks come in backwards
        tasks.reverse()
    for task in tasks:
        if not reexecute:
            wfi.add_task(task)
        metadata = wfi.get_task_metadata(task)
        metadata['workdir'] = wf_workdir
        wfi.set_task_metadata(task, metadata)
        db.workflows.add_task(task.id, wf_id, task.name, "WAITING")

    db.workflows.update_gdb_pid(wf_id, gdb_pid)
    wf_utils.update_wf_status(wf_id, 'Waiting')
    db.workflows.update_workflow_state(wf_id, 'Waiting')
    if no_start:
        log.info('Not starting workflow, as requested')
    else:
        log.info('Starting workflow')
        db.workflows.update_workflow_state(wf_id, 'Running')
        wf_utils.start_workflow(wf_id)


db_path = wf_utils.get_db_path()


class WFList(Resource):
    """Interacts with existing workflows."""

    def get(self):
        """Return list of workflows to client."""
        db = connect_db(wfm_db, db_path)
        workflow_list = db.workflows.get_workflows()
        info = []
        for wf_info in workflow_list:
            wf_id = wf_info.workflow_id
            wf_status = wf_info.state
            wf_name = wf_info.name
            info.append([wf_name, wf_id, wf_status])
        resp = make_response(jsonify(workflow_list=jsonpickle.encode(info)), 200)
        return resp

    def post(self):
        """Upload a workflow, initialize database, and start if required."""
        db = connect_db(wfm_db, db_path)
        reqparser = reqparse.RequestParser()
        reqparser.add_argument('wf_name', type=str, required=True,
                               location='form')
        reqparser.add_argument('wf_filename', type=str, required=True,
                               location='form')
        reqparser.add_argument('workdir', type=str, required=True,
                               location='form')
        reqparser.add_argument('workflow', type=str, required=True,
                               location='form')
        reqparser.add_argument('tasks', type=str, required=True,
                               location='form')
        reqparser.add_argument('no_start', type=str, required=True, location='form')
        reqparser.add_argument('workflow_archive', type=FileStorage, required=False,
                               location='files')
        data = reqparser.parse_args()
        wf_tarball = data['workflow_archive']
        wf_filename = data['wf_filename']
        wf_name = data['wf_name']
        wf_workdir = data['workdir']
        # Note we have to check for the 'true' string value
        no_start = data['no_start'].lower() == 'true'
        workflow = jsonpickle.decode(data['workflow'])
        # May have to decode the list and task objects separately
        tasks = [jsonpickle.decode(task) if isinstance(task, str) else task
                 for task in jsonpickle.decode(data['tasks'])]

        wf_id = workflow.id
        wf_dir = extract_wf(wf_id, wf_filename, wf_tarball)
        bolt_port = wf_utils.get_open_port()
        http_port = wf_utils.get_open_port()
        https_port = wf_utils.get_open_port()

        db.workflows.init_workflow(wf_id, wf_name, wf_dir, bolt_port, http_port, https_port)
        init_workflow.delay(wf_id, wf_name, wf_dir, wf_workdir, bolt_port, http_port,
                            https_port, no_start, workflow=workflow, tasks=tasks)

        return make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)

    def put(self):
        """Reexecute a workflow."""
        db = connect_db(wfm_db, db_path)
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

        db.workflows.init_workflow(wf_id, wf_name, wf_dir, bolt_port, http_port, https_port)
        init_workflow.delay(wf_id, wf_name, wf_dir, wf_workdir, bolt_port, http_port,
                            https_port, no_start=False, reexecute=True)

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
