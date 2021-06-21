#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import argparse
import sys
import logging
import os

from flask import Flask, request
from flask_restful import Resource, Api

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.task as task
import beeflow.scheduler.resource_allocation as resource_allocation
import beeflow.scheduler.affinity_algorithm as affinity_algorithm
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging

flask_app = Flask(__name__)
api = Api(flask_app)

# List of all available resources
resources = []


class ResourcesHandler(Resource):
    """Resources handler.

    """

    @staticmethod
    def put():
        """Create a list of resources to use for allocation.

        """
        resources.clear()
        #resources.extend([resource_allocation.Resource.decode(r)
        #                  for r in request.json])
        resources.extend(request.json)
        return 'created %i resource(s)' % len(resources)

    @staticmethod
    def get():
        """Get a list of all resources.

        """
        # return [r.encode() for r in resources]
        return resources


class WorkflowJobHandler(Resource):
    """Handle scheduling of workflow jobs.

    Schedule jobs for a specific workflow with the current resources.
    """

    @staticmethod
    def put(workflow_name):
        """Schedule a list of independent tasks.

        Schedules a new list of independent tasks with available resources.
        """
        data = request.json
        # tasks = [task.Task.decode(t) for t in data]
        tasks = data
        # Pick the scheduling algorithm
        #algorithm = affinity_algorithm.AffinityAlgorithm()
        # algorithm = algorithms.choose(tasks, **vars(flask_app.sched_conf))
        # algorithm = algorithms.choose(tasks, use_mars=Config.conf.use_mars,
        #                              mars_model=Config.conf.mars_model)
        #algorithm.schedule_all(tasks, resources)
        #return [t.encode() for t in tasks]
        return affinity_algorithm.schedule_all(tasks, resources)


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')


# TODO: Remove the below function


def load_config():
    """Load the config data."""
    parser = argparse.ArgumentParser(description='BEE scheduler')
    parser.add_argument('conf_file', default=None, help='BEE configuration file')
    args = parser.parse_args()

    if args.conf_file is not None:
        bc = BeeConfig(userconfig=args.conf_file)
    else:
        bc = BeeConfig()

    bee_workdir = bc.userconfig.get('DEFAULT','bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='sched.log')
    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)
    # Flask logging
    flask_app.logger.addHandler(handler) # noqa

    listen_port = bc.userconfig.get('scheduler', 'listen_port')
    return {
        'workdir': os.path.join(bee_workdir, 'scheduler'),
        'listen_port': listen_port,
    }


if __name__ == '__main__':
    conf = load_config()

    # Create the scheduler workdir, if necessary
    os.makedirs(conf['workdir'], exist_ok=True)

    flask_app.run(debug=True, port=conf['listen_port'])

# Ignore todo's or pylama fails
# pylama:ignore=W0511
