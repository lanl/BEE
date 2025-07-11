"""The workflow list module.

This contains endpoints forsubmitting, starting, and reexecuting workflows.
"""

import base64
import os
import subprocess
from beeflow.common.gdb.neo4j_driver import Neo4jDriver
import jsonpickle

from flask import request
from pydantic_core import ValidationError
from flask_restful import Resource
from celery import shared_task

from beeflow.common import log as bee_logging

# from beeflow.common.wf_profiler import WorkflowProfiler

from beeflow.wf_manager.models import (
    CopyWorkflowRequest,
    CopyWorkflowResponse,
    ListWorkflowsResponse,
    SubmitWorkflowRequest,
    SubmitWorkflowResponse,
    WorkflowInfo,
)
from beeflow.wf_manager.resources import wf_utils

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
    with open(archive_path, "wb") as archive_file:
        archive_file.write(base64.b64decode(encoded_archive_tarball))
    cwl_dir = wf_dir + "/cwl_files"

    os.mkdir(cwl_dir)
    subprocess.run(
        ["tar", "-xf", archive_path, "--strip-components=1", "-C", cwl_dir], check=False
    )
    return cwl_dir


@shared_task(ignore_result=True)
def init_workflow(
    wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow=None, tasks=None
):
    """Initialize the workflow in a separate process."""
    db = connect_db(wfm_db, db_path)
    wf_utils.connect_neo4j_driver(db.info.get_port("bolt"))
    wf_utils.setup_workflow(
        wf_id, wf_name, wf_dir, wf_workdir, no_start, workflow, tasks
    )


db_path = wf_utils.get_db_path()


class WFList(Resource):
    """Interacts with existing workflows."""

    def get(self):
        """Return list of workflows to client."""
        db = connect_db(wfm_db, db_path)
        wf_utils.connect_neo4j_driver(db.info.get_port("bolt"))
        info = Neo4jDriver().get_all_workflow_info()

        return ListWorkflowsResponse(workflow_info_list=info).model_dump(), 200

    def post(self):
        """Upload a workflown and start."""
        db = connect_db(wfm_db, db_path)
        try:
            data = SubmitWorkflowRequest.model_validate(request.json)
        except ValidationError as e:
            log.error(f"Error parsing request data: {e}")
            return (
                SubmitWorkflowResponse(
                    msg="Invalid request data", status="error", wf_id=None
                ).model_dump(),
                400,
            )

        wf_id = data.workflow.id
        wf_dir = extract_wf(wf_id, data.wf_filename, data.encoded_tarball)

        init_workflow.delay(
            wf_id,
            data.wf_name,
            wf_dir,
            data.wf_workdir,
            data.no_start,
            workflow=data.workflow,
            tasks=data.tasks,
        )

        return (
            SubmitWorkflowResponse(
                msg="Workflow uploaded", status="ok", wf_id=wf_id
            ).model_dump(),
            201,
        )

    def patch(self):
        """Copy workflow archive."""
        wf_id = CopyWorkflowRequest.model_validate(request.json).wf_id
        archive_dir = bc.get("DEFAULT", "bee_archive_dir")
        archive_path = os.path.join(archive_dir, wf_id + ".tgz")
        with open(archive_path, "rb") as archive:
            archive_file = jsonpickle.encode(archive.read())
        archive_filename = os.path.basename(archive_path)
        return (
            CopyWorkflowResponse(
                archive_file_pickle=archive_file, archive_filename=archive_filename
            ).model_dump(),
            200,
        )
