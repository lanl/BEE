"""This module contains the workflow action endpoints."""

import shutil
import os

from flask import request
from flask_restful import Resource, reqparse
from beeflow.common import log as bee_logging
from beeflow.wf_manager.resources import wf_utils
from beeflow.wf_manager.resources.wf_update import archive_workflow

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.wf_manager.models import (
    WorkflowActionResponse,
    ModifyWorkflowRequest,
    WorkflowStatusResponse,
)

log = bee_logging.setup(__name__)
db_path = wf_utils.get_db_path()


class WFActions(Resource):
    """Class to perform actions on existing workflows."""

    def __init__(self):
        """Initialize with passed json object."""
        self.reqparse = reqparse.RequestParser()

    def post(self, wf_id):
        """Start workflow. Send ready tasks to the task manager."""
        if wf_utils.start_workflow(wf_id):
            resp = (
                WorkflowActionResponse(
                    msg="Workflow started successfully"
                ).model_dump(),
                200,
            )
        else:
            resp = (
                WorkflowActionResponse(
                    msg="Cannot start workflow it is {state.lower()}."
                ).model_dump(),
                200,
            )
        return resp

    @staticmethod
    def get(wf_id):
        """Check the database for the current status of all tasks."""
        wfi = wf_utils.get_workflow_interface(wf_id)

        wf_status = wf_utils.get_wf_status(wf_id)
        if not wf_status:
            log.info(f"Workflow {wf_id} not found in the database.")
            return (
                WorkflowStatusResponse(
                    tasks_status=[],
                    wf_status="Not Found",
                    msg="Workflow not found",
                ).model_dump(),
                404,
            )

        tasks = wfi.get_tasks()
        tasks_status = []
        for task in tasks:
            state = wfi.get_task_state(task.id)
            tasks_status.append((task.id, task.name, state))

        return (
            WorkflowStatusResponse(
                tasks_status=tasks_status,
                wf_status=wf_status,
                msg="Workflow status retrieved successfully",
            ).model_dump(),
            200,
        )

    def delete(self, wf_id):
        """Cancel or delete the workflow. For cancel, current tasks finish running."""
        option = ModifyWorkflowRequest.model_validate(request.json).option
        if option == "cancel":
            wf_state = wf_utils.get_wf_status(wf_id)
            # Remove all tasks currently in the database
            wf_utils.update_wf_status(wf_id, "Cancelled")
            log.info(f"Workflow {wf_id} cancelled")
            # Archive cancelled workflow if it was originally paused
            if wf_state == "Paused":
                archive_workflow(wf_id, final_state="Cancelled")
            resp = (
                WorkflowActionResponse(
                    msg="Workflow cancelled successfully",
                ).model_dump(),
                202,
            )
        elif option == "remove":
            log.info(f"Removing workflow {wf_id}.")
            # TODO: Find how to delete in gdb
            resp = (
                WorkflowActionResponse(
                    msg="Workflow removed successfully",
                ).model_dump(),
                202,
            )
            bee_workdir = wf_utils.get_bee_workdir()
            workflow_dir = f"{bee_workdir}/workflows/{wf_id}"
            shutil.rmtree(workflow_dir, ignore_errors=True)
            archive_dir = bc.get("DEFAULT", "bee_archive_dir")
            archive_path = f"{archive_dir}/{wf_id}.tgz"
            if os.path.exists(archive_path):
                os.remove(archive_path)
        else:
            log.error(f"Invalid option '{option}' provided for workflow deletion.")
            resp = (
                WorkflowActionResponse(msg=f"Invalid option '{option}'").model_dump(),
                500,
            )

        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        option = ModifyWorkflowRequest.model_validate(request.json).option

        log.info("Pausing/resuming workflow")
        wf_state = wf_utils.get_wf_status(wf_id)
        if option == "pause" and wf_state in ("Running", "Initializing"):
            wf_utils.update_wf_status(wf_id, "Paused")
            log.info(f"Workflow {wf_id} Paused")
            resp = WorkflowActionResponse(msg="Workflow Paused").model_dump(), 200
        elif option == "resume" and wf_state == "Paused":
            wf_utils.update_wf_status(wf_id, "Running")
            wfi = wf_utils.get_workflow_interface(wf_id)
            tasks = wfi.get_ready_tasks()
            wf_utils.schedule_submit_tasks(wf_id, tasks)
            log.info(f"Workflow {wf_id} Resumed")
            resp = WorkflowActionResponse(msg="Workflow Resumed").model_dump(), 200
        else:
            resp_msg = f"Cannot {option} workflow. It is currently {wf_state.lower()}."
            log.info(resp_msg)
            resp = WorkflowActionResponse(msg=resp_msg).model_dump(), 200
        return resp
