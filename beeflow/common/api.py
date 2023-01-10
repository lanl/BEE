"""BeeApi wrapper around Flask-Restful for handling exceptions."""
import traceback
from flask import make_response, jsonify
from flask_restful import Api


class BeeApi(Api):
    """Wrapper around Flask-Restful's API to catch exceptions."""

    def handle_error(self, e):  # noqa (conflict on naming in base class vs. following convention)
        """Handle an error or exception."""
        return make_response(jsonify(error=traceback.format_exc()), 500)
