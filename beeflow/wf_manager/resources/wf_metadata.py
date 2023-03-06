"""Workflow endpoints for getting metadata."""

from flask import make_response, jsonify
from flask_restful import Resource
from beeflow.wf_manager.common import wf_db


class WFMetadata(Resource):
    """Class for getting metadata."""

    def get(self, wf_id):
        """Get and return metadata."""
        # For now, just get the bolt port. Later we may want to add more information here.
        bolt_port = wf_db.get_bolt_port(wf_id)
        metadata = {
            'bolt_port': bolt_port,
        }
        return make_response(jsonify(metadata), 200)
