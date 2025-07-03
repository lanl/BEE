"""The workflow list module.

This contains endpoints forsubmitting, starting, and reexecuting workflows.
"""

import base64
import os
import subprocess
import jsonpickle

from flask import make_response, jsonify, request
from pydantic_core import ValidationError
from werkzeug.datastructures import FileStorage
from flask_restful import Resource, reqparse
from celery import shared_task

from beeflow.common import log as bee_logging
# from beeflow.common.wf_profiler import WorkflowProfiler

from beeflow.wf_manager.models import ListWorkflowsResponse, SubmitWorkflowRequest, SubmitWorkflowResponse, WorkflowInfo
from beeflow.wf_manager.resources import wf_utils
from beeflow.common import object_models

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db
from beeflow.common.config_driver import BeeConfig as bc

log = bee_logging.setup(__name__)


# def initialize_wf_profiler(wf_name):
#    # Initialize the workflow profiling code
#    bee_workdir = wf_utils.get_bee_workdir()
#    fname = '{}.json'.format(wf_name)
#    profile_dir = os.path.join(bee_workdir, 'profiles')
#    os.makedirs(profile_dir, exist_ok=True)
#    output_path = os.path.join(profile_dir, fname)
#    wf_profiler = WorkflowProfiler(wf_name, output_path)


def extract_wf(wf_id, filename, encoded_archive_tarball):
    """Extract a workflow into the workflow directory."""
    wf_utils.create_workflow_dir(wf_id)
    wf_dir = wf_utils.get_workflow_dir(wf_id)
    archive_path = os.path.join(wf_dir, filename)
    with open(archive_path, 'wb') as archive_file:
        archive_file.write(base64.b64decode(encoded_archive_tarball))
    cwl_dir = wf_dir + "/cwl_files"

    os.mkdir(cwl_dir)
    subprocess.run(['tar', '-xf', archive_path, '--strip-components=1', '-C', cwl_dir],
                   check=False)
    return cwl_dir


@shared_task(ignore_result=True)
def init_workflow(wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow=None,
                  tasks=None):
    """Initialize the workflow in a separate process."""
    db = connect_db(wfm_db, db_path)
    wf_utils.connect_neo4j_driver(db.info.get_port('bolt'))
    wf_utils.setup_workflow(wf_id, wf_name, wf_dir, wf_workdir, no_start,
                            workflow, tasks)


db_path = wf_utils.get_db_path()


class WFList(Resource):
    """Interacts with existing workflows."""

    def get(self):
        """Return list of workflows to client."""
        db = connect_db(wfm_db, db_path)
        workflow_list = db.workflows.get_workflows()
        info = []
        for workflow in workflow_list:
            info.append(WorkflowInfo(wf_id=workflow.workflow_id,
                                     wf_name=workflow.name,
                                     wf_status=workflow.state))
        return ListWorkflowsResponse(workflow_info_list=info).model_dump(), 200

    def post(self):
        """Upload a workflown and start."""
        db = connect_db(wfm_db, db_path)
        try:
            data = SubmitWorkflowRequest.model_validate(request.json)
        except ValidationError as e:
            log.error(f"Error parsing request data: {e}")
            return SubmitWorkflowResponse(
                msg='Invalid request data',
                status='error',
                wf_id=None
            ).model_dump(), 400

        wf_id = data.workflow.id
        wf_dir = extract_wf(wf_id, data.wf_filename, data.encoded_tarball)

        db.workflows.init_workflow(wf_id, data.wf_name, wf_dir)

        init_workflow.delay(wf_id, data.wf_name, wf_dir, data.wf_workdir,
                            data.no_start, workflow=data.workflow, tasks=data.tasks)

        return SubmitWorkflowResponse(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id).model_dump(), 201

    def put(self):  # This method can be deleted / deprecated
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

        wf_id = object_models.generate_workflow_id()
        wf_dir = extract_wf(wf_id, wf_filename, workflow_archive)

        db.workflows.init_workflow(wf_id, wf_name, wf_dir)
        init_workflow.delay(wf_id, wf_name, wf_dir, wf_workdir, no_start=False)

        # Returnid and created
        resp = make_response(jsonify(msg='Workflow uploaded', status='ok',
                             wf_id=wf_id), 201)
        return resp

    def patch(self):
        """Copy workflow archive."""
        reqparser = reqparse.RequestParser()
        data = reqparser.parse_args()
        wf_id = data['wf_id']
        archive_dir = bc.get('DEFAULT', 'bee_archive_dir')
        archive_path = os.path.join(archive_dir, wf_id + '.tgz')
        with open(archive_path, 'rb') as archive:
            archive_file = jsonpickle.encode(archive.read())
        archive_filename = os.path.basename(archive_path)
        resp = make_response(jsonify(archive_file=archive_file,
                             archive_filename=archive_filename), 200)
        return resp
