#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import argparse

from flask import Flask, request
from flask_restful import Resource, Api

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types


# TODO: Grab this info from the config
SCHEDULER_PORT = 5100

flask_app = Flask(__name__)
api = Api(flask_app)

# List of all available resources
resources = []


class ResourcesHandler(Resource):
    """Resources handler.

    Handle creation of resources.
    """

    def put(self):
        """Create a list of resources to use for allocation.

        Create new resources based on a list of resources.
        """
        resources.clear()
        resources.extend([sched_types.Resource.decode(r) for r in request.json])
        return 'created %i resource(s)' % len(resources)

    def get(self):
        """Get a list of all resources.

        Returna a list of all available resources known to the scheduler.
        """
        return [r.encode() for r in resources]


class WorkflowJobHandler(Resource):
    """Handle scheduling of workflow jobs.

    Schedule jobs for a specific workflow with the current resources.
    """

    def put(self, workflow_name):
        """Schedule a list of independent tasks.

        Schedules a new list of independent tasks with available resources.
        """
        data = request.json
        tasks = [sched_types.Task.decode(t) for t in data]
        algorithm = algorithms.choose()
        allocation.schedule_all(algorithm, tasks, resources)
        return [t.encode() for t in tasks]


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')

if __name__ == '__main__':
    # TODO: Add -p port parsing
    parser = argparse.ArgumentParser(description='start the BEE scheduler')
    parser.add_argument('-p', dest='port', type=int, help='port to run on',
                        default=SCHEDULER_PORT)
    args = parser.parse_args()
    flask_app.run(debug=True, port=args.port)
