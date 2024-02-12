"""Task Manager app and api set up code.

Submits, cancels and monitors states of tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import atexit
import sys
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, make_response
from beeflow.common.api import BeeApi
from beeflow.task_manager.task_submit import TaskSubmit
from beeflow.task_manager.task_actions import TaskActions
from beeflow.task_manager.background import process_queues
from beeflow.common.config_driver import BeeConfig as bc


def create_app():
    """Create the flask app and add the REST endpoints for the TM."""
    app = Flask(__name__)
    api = BeeApi(app)

    # Endpoints
    api.add_resource(TaskSubmit, '/bee_tm/v1/task/submit/')
    api.add_resource(TaskActions, '/bee_tm/v1/task/')

    @app.route('/status')
    def get_status():
        """Report the current status of the Task Manager."""
        return make_response(jsonify(stauts='up'), 200)

    # Start the background scheduler and make sure it gets cleaned up
    if "pytest" not in sys.modules:
        scheduler = BackgroundScheduler({'apscheduler.timezone': 'UTC'})
        scheduler.add_job(func=process_queues, trigger="interval",
                          seconds=bc.get('task_manager', 'background_interval'))
        scheduler.start()

        # This kills the scheduler when the process terminates
        # so we don't accidentally leave a zombie process
        atexit.register(scheduler.shutdown)

    return app
