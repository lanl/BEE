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
        resources.extend([resource_allocation.Resource.decode(r)
                          for r in request.json])
        return 'created %i resource(s)' % len(resources)

    @staticmethod
    def get():
        """Get a list of all resources.

        """
        return [r.encode() for r in resources]


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
        tasks = [task.Task.decode(t) for t in data]
        # Pick the scheduling algorithm
        algorithm = algorithms.choose(tasks, **vars(flask_app.sched_conf))
        # algorithm = algorithms.choose(tasks, use_mars=Config.conf.use_mars,
        #                              mars_model=Config.conf.mars_model)
        algorithm.schedule_all(tasks, resources)
        return [t.encode() for t in tasks]


api.add_resource(ResourcesHandler, '/bee_sched/v1/resources')
api.add_resource(WorkflowJobHandler,
                 '/bee_sched/v1/workflows/<string:workflow_name>/jobs')

# Default config values
SCHEDULER_PORT = 5100
# TODO: Use MODEL_FILE when interacting with MARS scheduling
MODEL_FILE = 'model'
ALLOC_LOGFILE = 'schedule_trace.txt'
MARS_CNT = 4
DEFAULT_ALGORITHM = 'fcfs'


def load_config_values():
    """Load the config, if necessary, and return config values.

    Load the config, if necessary, and return config values. Pulls initial
    config values from command line arguments.
    """
    parser = argparse.ArgumentParser(description='start the BEE scheduler')
    parser.add_argument('-p', dest='port', type=int, help='port to run on',
                        default=SCHEDULER_PORT)
    parser.add_argument('--log', dest='log',
                        help='Scheduler log file location')
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
    parser.add_argument('--allog-logfile', dest='alloc_logfile',
                        help='logfile/trace file to write to')
    parser.add_argument('--default-algorithm', dest='default_algorithm',
                        help='default algorithm to use')
    parser.add_argument('--algorithm', dest='algorithm',
                        help='specific algorithm to use')
    parser.add_argument('--workdir', dest='workdir',
                        help='workdir to use for the scheduler')
    args = parser.parse_args()
    # Set the default config values
    conf = {
        'log': args.log,
        'listen_port': args.port,
        'use_mars': args.use_mars,
        'mars_model': args.mars_model,
        'mars_task_cnt': args.mars_task_cnt,
        'alloc_logfile': args.alloc_logfile,
        'algorithm': args.algorithm,
        'default_algorithm': args.default_algorithm,
        'workdir': args.workdir,
    }
    if args.read_config:
        # Read config values from the config file
        if args.config_file is not None:
            bc = BeeConfig(userconfig=args.config_file) # noqa
        else:
            bc = BeeConfig() # noqa

        if bc.userconfig.has_section('scheduler'):
            for key in bc.userconfig['scheduler']:
                conf[key] = bc.userconfig['scheduler'].get(key)
        else:
            log.info('[scheduler] section not found in configuration file, '
                    'default values will be added')
            bc.modify_section('user', 'scheduler', conf)
            sys.exit(f'Please check {bc.userconfig_file} and restart '
                     'Scheduler')
        bee_workdir = bc.userconfig['DEFAULT'].get('bee_workdir')
        # Set some defaults
        if not conf['log']:
            conf['log'] = '/'.join([bee_workdir, 'logs', 'sched.log'])
        if not conf['workdir']:
            conf['workdir'] = os.path.join(bee_workdir, 'scheduler')
        if not conf['alloc_logfile']:
            conf['alloc_logfile'] = os.path.join(conf['workdir'],
                                                 ALLOC_LOGFILE)
    else:
        # Don't read from the config
        if not conf['log']:
            conf['log'] = 'sched.log'
        if not conf['workdir']:
            conf['workdir'] = os.getcwd()
        if not conf['alloc_logfile']:
            conf['alloc_logfile'] = ALLOC_LOGFILE

    conf = argparse.Namespace(**conf)
    log.info('Config = [')
    log.info(f'\tlisten_port = {conf.listen_port}')
    log.info(f'\tuse_mars = {conf.use_mars}')
    log.info(f'\tmars_model = {conf.mars_model}')
    log.info(f'\tmars_task_cnt = {conf.mars_task_cnt}')
    log.info(f'\talloc_logfile = {conf.alloc_logfile}')
    log.info(f'\talgorithm = {conf.algorithm}')
    log.info(f'\tdefault_algorithm = {conf.default_algorithm}')
    log.info(f'\tworkdir = {conf.workdir}')
    log.info(']')
    return conf, bc


if __name__ == '__main__':
    CONF, bc = load_config_values()
    handler = bee_logging.save_log(bc, log, logfile='sched.log')
    flask_app.sched_conf = CONF
    # Load algorithm data
    algorithms.load(**vars(CONF))

    # Create the scheduler workdir, if necessary
    os.makedirs(CONF.workdir, exist_ok=True)

    # Werkzeug logging
    werk_log = logging.getLogger('werkzeug')
    werk_log.setLevel(logging.INFO)
    werk_log.addHandler(handler)

    # Flask logging
    flask_app.logger.addHandler(handler) # noqa
    flask_app.run(debug=True, port=CONF.listen_port)

# Ignore todo's or pylama fails
# pylama:ignore=W0511
