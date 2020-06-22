#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import os
import sys
import math
import allocation

from flask import Flask, jsonify, make_response, request
from flask_restful import Resource, Api, reqparse


flask_app = Flask(__name__)
api = Api(flask_app)

class ScheduleHandler(Resource):
    """Schedule handler.

    Perform scheduling operations.
    """

    def put(self, name=None):
        """Send a workflow, cluster information, etc. to get scheduled.

        Schedule the workflow using a variety of algorithms to map it to the
        underlying cluster and nodes available.
        :param name: name of the workflow
        :type name: str
        """
        data = request.json
        workflow = allocation.Workflow.decode(data['workflow'])
        clusters = [allocation.Cluster.decode(cluster)
                    for cluster in data['clusters']]
        provisions = allocation.fcfs(workflow=workflow, clusters=clusters,
                                     start_time=data['start_time'])
        # Encode allocation time slots
        return {name: provisions[name].encode() for name in provisions}


api.add_resource(ScheduleHandler, '/bee_sched/v1/schedule')

if __name__ == '__main__':
    flask_app.run(debug=True, port=5100)
