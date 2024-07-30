"""This module contains the workflow action endpoints."""
import shutil
import os

from flask import make_response, jsonify
from flask_restful import Resource, reqparse
from beeflow.common import log as bee_logging
from beeflow.wf_manager.resources import wf_utils

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db

log = bee_logging.setup(__name__)
db_path = wf_utils.get_db_path()


class WFActions(Resource):
    """Class to perform actions on existing workflows."""

    def __init__(self):
        """Initialize with passed json object."""
        self.reqparse = reqparse.RequestParser()

    def post(self, wf_id):
        """Start workflow. Send ready tasks to the task manager."""
        db = connect_db(wfm_db, db_path)
        if wf_utils.start_workflow(wf_id):
            db.workflows.update_workflow_state(wf_id, 'Running')
            resp = make_response(jsonify(msg='Started workflow!', status='ok'), 200)
        else:
            resp_body = jsonify(msg='Cannot start workflow it is {state.lower()}.', status='ok')
            resp = make_response(resp_body, 200)
        return resp

    @staticmethod
    def get(wf_id):
        """Check the database for the current status of all tasks."""
        db = connect_db(wfm_db, db_path)
        tasks = db.workflows.get_tasks(wf_id)
        tasks_status = []
        if not tasks:
            log.info(f"Bad query for wf {wf_id}.")
            wf_status = 'No workflow with that ID is currently loaded'
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='not found'), 404)

        for task in tasks:
            tasks_status.append((task.id, task.name, task.state))
        wf_status = db.workflows.get_workflow_state(wf_id)

        resp = make_response(jsonify(tasks_status=tasks_status,
                             wf_status=wf_status, status='ok'), 200)
        return resp

    def delete(self, wf_id):
        """Cancel or delete the workflow. For cancel, current tasks finish running."""
        self.reqparse.add_argument('option', type=str, location='json')
        option = self.reqparse.parse_args()['option']
        db = connect_db(wfm_db, db_path)
        if option == "cancel":
            wfi = wf_utils.get_workflow_interface(wf_id)
            # Remove all tasks currently in the database
            wfi.set_workflow_state('Cancelled')
            wf_utils.update_wf_status(wf_id, 'Cancelled')
            db.workflows.update_workflow_state(wf_id, 'Cancelled')
            log.info(f"Workflow {wf_id} cancelled")
            resp = make_response(jsonify(status='Cancelled'), 202)
        elif option == "remove":
            log.info(f"Removing workflow {wf_id}.")
            db.workflows.delete_workflow(wf_id)
            resp = make_response(jsonify(status='Removed'), 202)
            bee_workdir = wf_utils.get_bee_workdir()
            workflow_dir = f"{bee_workdir}/workflows/{wf_id}"
            shutil.rmtree(workflow_dir, ignore_errors=True)
            archive_path = f"{bee_workdir}/archives/{wf_id}.tgz"
            if os.path.exists(archive_path):
                os.remove(archive_path)
        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        db = connect_db(wfm_db, db_path)
        self.reqparse.add_argument('option', type=str, location='json')
        option = self.reqparse.parse_args()['option']

        wfi = wf_utils.get_workflow_interface(wf_id)
        log.info('Pausing/resuming workflow')
        wf_state = wfi.get_workflow_state()
        if option == 'pause' and wf_state in ('RUNNING', 'INITIALIZING'):
            wfi.pause_workflow()
            wf_utils.update_wf_status(wf_id, 'Paused')
            db.workflows.update_workflow_state(wf_id, 'Paused')
            log.info(f"Workflow {wf_id} Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
        elif option == 'resume' and wf_state == 'PAUSED':
            wfi.resume_workflow()
            tasks = wfi.get_ready_tasks()
            wf_utils.schedule_submit_tasks(wf_id, tasks)
            wf_utils.update_wf_status(wf_id, 'Running')
            db.workflows.update_workflow_state(wf_id, 'Running')
            log.info(f"Workflow {wf_id} Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
        else:
            resp_msg = f'Cannot {option} workflow. It is currently {wf_state.lower()}.'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
        return resp
