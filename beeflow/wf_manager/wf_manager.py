"""Start up the workflow manager connecting all of the endpoints."""

from flask import Flask
from flask_restful import Api
from beeflow.common.config_driver import BeeConfig as bc

from beeflow.wf_manager.resources.wf_list import WFList
from beeflow.wf_manager.resources.wf_actions import WFActions
from beeflow.wf_manager.resources.wf_update import WFUpdate

from beeflow.common.log import main_log as log
from beeflow.wf_manager.resources import wf_utils
import beeflow.common.log as bee_logging


def create_app():
    """Create flask app object and add REST endpoints."""
    app = Flask(__name__)
    api = Api(app)

    # Add endpoints
    api.add_resource(WFList, '/bee_wfm/v1/jobs/')
    api.add_resource(WFActions, '/bee_wfm/v1/jobs/<string:wf_id>')
    api.add_resource(WFUpdate, '/bee_wfm/v1/jobs/update/')
    return app


if __name__ == '__main__':
    flask_app = create_app()
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    bee_workdir = wf_utils.get_bee_workdir()
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')
    flask_app.run(debug=False, port=str(wfm_listen_port))
