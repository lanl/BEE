"""Handle task submission."""
import traceback
from flask import jsonify, make_response, request
from flask_restful import Resource, reqparse
import jsonpickle
from pydantic import ValidationError
from beeflow.common import log as bee_logging
from beeflow.task_manager import utils
from beeflow.task_manager.models import SubmitTasksRequest, TaskActionResponse

log = bee_logging.setup(__name__)


class TaskActions(Resource):
    """API for task actions."""

    @staticmethod
    def post():
        """Receives tasks from WFM."""
        db = utils.connect_db()
        try:
            tasks = SubmitTasksRequest.model_validate(request.json).tasks
        except Exception as err:
            log.error(f"Invalid request data: {err}")
            return TaskActionResponse(msg=str(err)), 400
        for task in tasks:
            db.submit_queue.push(task)
            log.info(f"Added {task.name} task to the submit queue")
        return TaskActionResponse(
            msg='Tasks submitted successfully'
        ).model_dump(), 200
    
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
            except Exception as err: # pylint: disable=W0718 # we have to catch everything here
                log.error(err)
                log.error(traceback.format_exc())
                job_state = 'ZOMBIE'
            cancel_msg += f"{name} {task_id} {job_id} {job_state}"
        db.job_queue.clear()
        db.submit_queue.clear()
        return TaskActionResponse(
            msg=f'Cancelled all tasks: {cancel_msg}'
        ).model_dump(), 200

