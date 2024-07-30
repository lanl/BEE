"""Start up the workflow manager connecting all of the endpoints."""

import os
from flask import Flask
from celery import Celery # noqa (pylama can't find celery imports)
from celery import shared_task #noqa
from beeflow.common.api import BeeApi
from beeflow.common import paths
from beeflow.wf_manager.resources.wf_list import WFList
from beeflow.wf_manager.resources.wf_actions import WFActions
from beeflow.wf_manager.resources.wf_metadata import WFMetadata
from beeflow.wf_manager.resources.wf_update import WFUpdate
from beeflow.wf_manager.resources import wf_utils


def create_app():
    """Create flask app object and add REST endpoints."""
    app = Flask(__name__)
    api = BeeApi(app)

    # Add endpoints
    api.add_resource(WFList, '/bee_wfm/v1/jobs/')
    api.add_resource(WFActions, '/bee_wfm/v1/jobs/<string:wf_id>')
    api.add_resource(WFMetadata, '/bee_wfm/v1/jobs/<string:wf_id>/metadata')
    api.add_resource(WFUpdate, '/bee_wfm/v1/jobs/update/')

    # Initialize celery app
    celery_app = Celery(app.name)
    redis_socket = os.path.join(paths.redis_root(), paths.redis_sock_fname())
    celery_app.config_from_object({
        'broker_url': f'redis+socket://{redis_socket}',
        'result_backend': f'db+sqlite://{paths.celery_db()}',
        'task_serializer': 'pickle',
        'accept_content': ['application/json', 'application/x-python-serialize'],
    })
    celery_app.set_default()
    app.extensions['celery'] = celery_app

    return app


if __name__ == '__main__':
    flask_app = create_app()
    bee_workdir = wf_utils.get_bee_workdir()
    # handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='wf_manager.log')
    # wfm_listen_port = wf_utils.get_open_port()
    # wf_db.set_wfm_port(wfm_listen_port)
    # flask_app.run(debug=False, port=str(wfm_listen_port))
