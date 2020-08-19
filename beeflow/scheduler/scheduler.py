#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import argparse
import sys

from flask import Flask, request
from flask_restful import Resource, Api

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types
import beeflow.common.config.config_driver as config_driver


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
        resources.extend([sched_types.Resource.decode(r)
                          for r in request.json])
        return 'created %i resource(s)' % len(resources)

    def get(self):
        """Get a list of all resources.

        Return a list of all available resources known to the scheduler.
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
        # Pick the scheduling algorithm
        algorithm = algorithms.choose(tasks, use_mars=Config.conf.use_mars,
                                      mars_model=Config.conf.mars_model)
        allocation.schedule_all(algorithm, tasks, resources)
        return [t.encode() for t in tasks]


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')

# Default config values
SCHEDULER_PORT = 5100
# TODO: Use MODEL_FILE when interacting with MARS scheduling
MODEL_FILE='model'


def load_config_values():
    """Load the config, if necessary, and return config values.

    Load the config, if necessary, and return config values. Pulls initial
    config values from command line arguments.
    """
    parser = argparse.ArgumentParser(description='start the BEE scheduler')
    parser.add_argument('-p', dest='port', type=int, help='port to run on',
                        default=SCHEDULER_PORT)
    parser.add_argument('--no-config', dest='read_config',
                        help='do not read from the config',
                        action='store_false')
    parser.add_argument('--use-mars', dest='use_mars',
                        help='use the mars scheduling algorithm',
                        action='store_true')
    parser.add_argument('--mars-model', dest='mars_model',
                        help='mars model to load', default=MODEL_FILE)
    args = parser.parse_args()
    # Set the default config values
    conf = {
        'listen_port': args.port,
        'use_mars': args.use_mars,
        'mars_model': args.mars_model,
    }
    if args.read_config:
        try:
            bc = config_driver.BeeConfig(userconfig=sys.argv[1])
        except IndexError:
            bc = config_driver.BeeConfig()

        if bc.userconfig.has_section('scheduler'):
            conf['listen_port'] = bc.userconfig['scheduler'].get(
                'listen_port', SCHEDULER_PORT)
            conf['use_mars'] = bc.userconfig['scheduler'].get('use_mars',
                                                              False)
        else:
            print('[scheduler] section not found in configuration file, '
                  'default values will be added')
            bc.modify_section('user', 'scheduler', conf)
            sys.exit(f'Please check {bc.userconfig_file} and restart '
                     'Scheduler')
    print('Config = [')
    print(f'\tlisten_port {conf["listen_port"]}')
    print(f'\tuse_mars {conf["use_mars"]}')
    print(f'\tmars_model {conf["mars_model"]}')
    print(']')
    return argparse.Namespace(**conf)


class Config:
    pass


if __name__ == '__main__':
    conf = load_config_values()
    # Conf access should be set differently
    Config.conf = conf
    flask_app.run(debug=True, port=conf.listen_port)
