from flask import Flask
from flask_restful import Api
from beeflow.common.config_driver import BeeConfig

from beeflow.wf_manager.resources.jobs_list_rework import JobsList
from beeflow.wf_manager.resources.job_actions import JobActions
from beeflow.wf_manager.resources.job_update import JobUpdate

def create_app():
    """ Create flask app object and add REST endpoints"""
    app = Flask(__name__)
    api = Api(app)

    # Add endpoints
    api.add_resource(JobsList, '/bee_wfm/v1/jobs/')
    api.add_resource(JobActions, '/bee_wfm/v1/jobs/<string:wf_id>')
    api.add_resource(JobUpdate, '/bee_wfm/v1/jobs/update/')
    return app


if __name__ == '__main__':
    app = create_app()
    bc = BeeConfig()
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    app.run(debug=True, port=str(wfm_listen_port))
