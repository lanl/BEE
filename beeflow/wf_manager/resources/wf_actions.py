"""This module contains the workflow action endpoints."""

from flask import make_response, jsonify
from flask_restful import Resource, reqparse
from beeflow.wf_manager.common import wf_db
from beeflow.common import log as bee_logging
from beeflow.wf_manager.resources import wf_utils


log = bee_logging.setup(__name__)


class WFActions(Resource):
    """Class to perform actions on existing workflows."""

    def __init__(self):
        """Initialize with passed json object."""
        self.reqparse = reqparse.RequestParser()

    def post(self, wf_id):
        """Start workflow. Send ready tasks to the task manager."""
        wfi = wf_utils.get_workflow_interface(wf_id)
        state = wfi.get_workflow_state()
        if state in ('RUNNING', 'PAUSED', 'COMPLETED'):
            resp = make_response(jsonify(msg='Cannot start workflow it is '
                                 f'{state.lower()}.',
                                         status='ok'), 200)
            return resp
        wfi.execute_workflow()
        tasks = wfi.get_ready_tasks()
        wf_utils.schedule_submit_tasks(wf_id, tasks)
        wf_id = wfi.workflow_id
        wf_utils.update_wf_status(wf_id, 'Running')
        wf_db.update_workflow_state(wf_id, 'Running')
        resp = make_response(jsonify(msg='Started workflow!', status='ok'), 200)
        return resp

    @staticmethod
    def get(wf_id):
        """Check the database for the current status of all tasks."""
        tasks = wf_db.get_tasks(wf_id)
        tasks_status = []
        if not tasks:
            log.info(f"Bad query for wf {wf_id}.")
            wf_status = 'No workflow with that ID is currently loaded'
            tasks_status.append('Unavailable')
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='not found'), 404)

        for task in tasks:
            tasks_status.append(f"{task.name}--{task.status}")
        tasks_status = '\n'.join(tasks_status)
        wf_status = wf_utils.read_wf_status(wf_id)

        resp = make_response(jsonify(tasks_status=tasks_status,
                             wf_status=wf_status, status='ok'), 200)
        return resp

    @staticmethod
    def delete(wf_id):
        """Cancel the workflow. Lets current tasks finish running."""
        wfi = wf_utils.get_workflow_interface(wf_id)
        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        wf_utils.update_wf_status(wf_id, 'Cancelled')
        wf_db.update_workflow_state(wf_id, 'Cancelled')
        wf_db.delete_workflow(wf_id)
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='Cancelled'), 202)
        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        self.reqparse.add_argument('option', type=str, location='json')
        option = self.reqparse.parse_args()['option']

        wfi = wf_utils.get_workflow_interface(wf_id)
        wf_state = wfi.get_workflow_state()
        if option == 'pause' and wf_state == 'RUNNING':
            wfi.pause_workflow()
            wf_utils.update_wf_status(wf_id, 'Paused')
            wf_db.update_workflow_state(wf_id, 'Paused')
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
        elif option == 'resume' and wf_state == 'PAUSED':
            wfi.resume_workflow()
            tasks = wfi.get_ready_tasks()
            wf_utils.schedule_submit_tasks(wf_id, tasks)
            wf_utils.update_wf_status(wf_id, 'Running')
            wf_db.update_workflow_state(wf_id, 'Running')
            log.info("Workflow Paused")
            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
        else:
            resp_msg = f'Cannot {option} workflow. It is currently {wf_state.lower()}.'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
        return resp
