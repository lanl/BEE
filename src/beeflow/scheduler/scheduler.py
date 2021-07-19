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
import beeflow.scheduler.affinity as affinity
import beeflow.scheduler.random_fcfs as random_fcfs
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging

flask_app = Flask(__name__)
api = Api(flask_app)

# dict of all available resources (should be in Redis)
resources = {}


# TODO: Need to document precisely all the properties that a resource may have
class ResourcesHandler(Resource):
    """Resources handler."""

    @staticmethod
    def put():
        """Create a list of resources to use for allocation."""
        resources.clear()
        resources.update(request.json)
        return 'created %i resource(s)' % len(resources)

    @staticmethod
    def get():
        """Get a list of all resources."""
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
        tasks = data
        if conf['algorithm'] == 'affinity':
            return affinity.schedule_all(tasks, resources)
        elif conf['algorithm'] == 'random_fcfs':
            return random_fcfs.schedule_all(tasks, resources)
        return None


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')


# TODO: Remove the below function


#def load_config():
#    """Load the config data."""

# Load the configuration
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
# Use a default algorithm of affinity
algorithm = bc.userconfig['scheduler'].get('algorithm', 'affinity')
conf = {
    'workdir': os.path.join(bee_workdir, 'scheduler'),
    'listen_port': listen_port,
    'algorithm': algorithm,
}
log.info('workdir: %s' % (conf['workdir'],))
log.info('listen_port: %s' % (conf['listen_port'],))
log.info('algorithm: %s' % (conf['algorithm'],))

# TODO: Maybe this check can be removed here
if __name__ == '__main__':
    # conf = load_config()

    # Create the scheduler workdir, if necessary
    os.makedirs(conf['workdir'], exist_ok=True)

    flask_app.run(debug=True, port=conf['listen_port'])


# TODO: Redo test cases

# Ignore todo's or pylama fails
# pylama:ignore=W0511
