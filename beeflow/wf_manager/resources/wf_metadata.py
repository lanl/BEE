"""Workflow metadata endpoints."""

from flask import make_response, jsonify
from flask_restful import Resource
from beeflow.wf_manager.common import wf_db
from beeflow.common import log as bee_logging


log = bee_logging.setup(__name__)


class WFMetadata(Resource):
    """Workflow metadata class."""

    def get(self, wf_id):
        """Return metadata about the given workflow."""
        data = {
            'bolt_port': wf_db.get_bolt_port(wf_id),
            'http_port': wf_db.get_http_port(wf_id),
            'https_port': wf_db.get_https_port(wf_id),
        }
        return make_response(jsonify(**data), 200)
