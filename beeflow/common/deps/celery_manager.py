"""Module for celery configuration."""
from beeflow.wf_manager.wf_manager import create_app


flask_app = create_app()
celery_app = flask_app.extensions['celery']
