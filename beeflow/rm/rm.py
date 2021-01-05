#!/usr/bin/env python3
"""Resource Monitor.

"""
from flask import Flask
from flask_restful import Resource, Api


app = Flask(__name__)
api = Api(app)

# TODO: Should slurm interface be in the worker code?

# Load BeeConfig
# TODO

# Note: The Resource Monitor will not cause any state changes, but will simply
# be able to report information about particular resources. This is why all end
# points will only support GET requests.

# /bee_rm/v1/nodes URL
class NodesResource(Resource):
    """
    """

    def get(self):
        """
        """
        pass
        # TODO


# /bee_rm/v1/partitions URL
class PartitionsResource(Resource):
    """
    """

    def get(self):
        """
        """
        pass
        # TODO


# /bee_rm/v1/reservations URL
class ReservationsResource(Resource):
    """
    """

    def get(self):
        """
        """
        pass
        # TODO


# /bee_rm/v1/qos URL
class QOSResource(Resource):
    """
    """

    def get(self):
        """
        """
        pass
        # TODO


api.add_resource(NodesResource, '/bee_rm/v1/nodes')
api.add_resource(PartitionsResource, '/bee_rm/v1/partitions')
api.add_resource(ReservationsResource, '/bee_rm/v1/reservations')
api.add_resource(QOSResource, '/bee_rm/v1/qos')

if __name__ == '__main__':
    # Running in debug mode
    app.run(debug=True)
    # TODO
