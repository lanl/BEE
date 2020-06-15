#!/usr/bin/env python3
import os
import sys

from flask import Flask, jsonify, make_response
from flask_restful import Resource, Api, reqparse

flask_app = Flask(__name__)
api = Api(flask_app)

class WorkflowManager(Resource):
    def post(self, name=None):
        pass

    def get(self, name=None):
        pass

    def put(self, name=None):
        pass

    def delete(self, name=None):
        pass


class AllocationManager(Resource):
    def post(self, name):
        """Start the scheduling algorithm."""
        pass

    def get(self, name):
        """
        Get the allocation that has been calculated or return current status.
        """
        pass


class PartitionManager(Resource):
    def post(self, name=None):
        pass

    def get(self, name=None):
        pass

    def put(self, name=None):
        pass

    def delete(self, name=None):
        pass


class NodeManager(Resource):
    def post(self, node_id=None):
        pass

    def get(self, node_id=None):
        pass

    def put(self, node_id=None):
        pass

    def delete(self, node_id=None):
        pass


api.add_resource(WorkflowManager, '/bee_sched/v1/workflows/',
                 '/bee_sched/v1/workflows/<string:name>')
api.add_resource(AllocationManager,
                 '/bee_sched/v1/workflows/<string:name>/allocation')
api.add_resource(PartitionManager, '/bee_sched/v1/partitions/',
                 '/bee_sched/v1/partitions/<string:name>')
api.add_resource(NodeManager, '/bee_sched/v1/nodes/',
                 '/bee_sched/v1/nodes/<int:node_id>')

if __name__ == '__main__':
    flask_app.run(debug=True, port=5100)
