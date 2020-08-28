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
        algorithm = algorithms.choose(tasks, **vars(flask_app.sched_conf))
        # algorithm = algorithms.choose(tasks, use_mars=Config.conf.use_mars,
        #                              mars_model=Config.conf.mars_model)
        allocation.schedule_all(algorithm, tasks, resources)
        return [t.encode() for t in tasks]


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')

# Default config values
SCHEDULER_PORT = 5100
# TODO: Use MODEL_FILE when interacting with MARS scheduling
MODEL_FILE = 'model'
LOGFILE = 'schedule_log.txt'
MARS_CNT = 4


def load_config_values():
    """Load the config, if necessary, and return config values.

    Load the config, if necessary, and return config values. Pulls initial
    config values from command line arguments.
    """
    parser = argparse.ArgumentParser(description='start the BEE scheduler')
    parser.add_argument('-p', dest='port', type=int, help='port to run on',
                        default=SCHEDULER_PORT)
    parser.add_argument('--config-file', dest='config_file',
                        help='location of config file')
    parser.add_argument('--no-config', dest='read_config',
                        help='do not read from the config',
                        action='store_false')
    parser.add_argument('--use-mars', dest='use_mars',
                        help='use the mars scheduling algorithm',
                        action='store_true')
    parser.add_argument('--mars-model', dest='mars_model',
                        help='mars model to load', default=MODEL_FILE)
    parser.add_argument('--mars-task-cnt', dest='mars_task_cnt',
                        help='number of tasks needed for scheduling with MARS',
                        default=MARS_CNT)
    parser.add_argument('--logfile', dest='logfile',
                        help='logfile to write to', default=LOGFILE)
    parser.add_argument('--algorithm', dest='algorithm',
                        help='specific algorithm to use')
    args = parser.parse_args()
    # Set the default config values
    conf = {
        'listen_port': args.port,
        'use_mars': args.use_mars,
        'mars_model': args.mars_model,
        'mars_task_cnt': args.mars_task_cnt,
        'logfile': args.logfile,
        'algorithm': args.algorithm,
    }
    if args.read_config:
        # Read config values from the config file
        if args.config_file is not None:
            bc = config_driver.BeeConfig(args.config_file)
        else:
            bc = config_driver.BeeConfig()

        if bc.userconfig.has_section('scheduler'):
            conf['listen_port'] = bc.userconfig['scheduler'].get(
                'listen_port', SCHEDULER_PORT)
            conf['use_mars'] = bc.userconfig['scheduler'].get('use_mars',
                                                              False)
            conf['mars_model'] = bc.userconfig['scheduler'].get(
                'mars_model', args.mars_model)
            conf['mars_task_cnt'] = bc.userconfig['scheduler'].get(
                'mars_task_cnt', args.mars_task_cnt)
            conf['logfile'] = bc.userconfig['scheduler'].get('logfile',
                                                             args.logfile)
            conf['algorithm'] = bc.userconfig['scheduler'].get('algorithm',
                                                               args.algorithm)
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
    print(f'\tmars_task_cnt {conf["mars_task_cnt"]}')
    print(f'\tlogfile {conf["logfile"]}')
    print(f'\talgorithm {conf["algorithm"]}')
    print(']')
    return argparse.Namespace(**conf)


if __name__ == '__main__':
    conf = load_config_values()
    flask_app.sched_conf = conf
    # Load algorithm data
    algorithms.load(**vars(conf))
    flask_app.run(debug=True, port=conf.listen_port)
