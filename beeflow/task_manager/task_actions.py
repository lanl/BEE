"""Manage actions for tasks coming from the WFM."""
import traceback
from flask import jsonify, make_response
from flask_restful import Resource
from beeflow.common import log as bee_logging
from beeflow.task_manager import utils

log = bee_logging.setup(__name__)


class TaskActions(Resource):
    """Actions to take for tasks."""

    @staticmethod
    def delete():
        """Cancel received from WFM to cancel job, update queue to monitor state."""
        db = utils.connect_db()
        worker = utils.worker_interface()
        cancel_msg = ""
        for job in db.job_queue:
            task_id = job.task.id
            job_id = job.job_id
            name = job.task.name
            log.info(f"Cancelling {name} with job_id: {job_id}")
            try:
                job_state = worker.cancel_task(job_id)
            except Exception as err: # noqa (we have to catch everything here)
                log.error(err)
                log.error(traceback.format_exc())
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        db.job_queue.clear()
        db.submit_queue.clear()
        resp = make_response(jsonify(msg=cancel_msg, status='ok'), 200)
        return resp
