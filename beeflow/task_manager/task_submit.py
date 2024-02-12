"""Handle task submission."""
from flask import jsonify, make_response
from flask_restful import Resource, reqparse
import jsonpickle
from beeflow.common import log as bee_logging
from beeflow.task_manager import utils

log = bee_logging.setup(__name__)


class TaskSubmit(Resource):
    """WFM sends tasks to the task manager."""

    @staticmethod
    def post():
        """Receives task from WFM."""
        db = utils.connect_db()
        parser = reqparse.RequestParser()
        parser.add_argument('tasks', type=str, location='json')
        data = parser.parse_args()
        tasks = jsonpickle.decode(data['tasks'])
        for task in tasks:
            db.submit_queue.push(task)
            log.info(f"Added {task.name} task to the submit queue")
        resp = make_response(jsonify(msg='Tasks Added!', status='ok'), 200)
        return resp
