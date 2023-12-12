#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import argparse
import os

from flask import Flask, request
from flask_restful import Resource, Api

from beeflow.scheduler import algorithms
from beeflow.scheduler import task
from beeflow.scheduler import resource_allocation
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.db import sched_db
from beeflow.common import log as bee_logging

from beeflow.common.db.bdb import connect_db

log = bee_logging.setup(__name__)

flask_app = Flask(__name__)
api = Api(flask_app)

bee_workdir = bc.get('DEFAULT', 'bee_workdir')
db_path = bee_workdir + '/' + 'sched.db'


class ResourcesHandler(Resource):
    """Resources handler."""

    @staticmethod
    def put():
        """Create a list of resources to use for allocation."""
        db = connect_db(sched_db, db_path)
        db.resources.clear()
        resources = [resource_allocation.Resource.decode(r)
                     for r in request.json]
        db.resources.extend(resources)
        return f'created {len(resources)} resource(s)'

    @staticmethod
    def get():
        """Get a list of all resources."""
        db = connect_db(sched_db, db_path)
        return [r.encode() for r in db.resources]


class WorkflowJobHandler(Resource):
    """Schedule jobs for a specific workflow with the current resources."""

    @staticmethod
    def put(workflow_name):  # noqa ('workflow_name' may be used in the future)
        """Schedules a new list of independent tasks with available resources."""
        db = connect_db(sched_db, db_path)
        data = request.json
        tasks = [task.Task.decode(t) for t in data]
        # Pick the scheduling algorithm
        algorithm = algorithms.choose(**vars(flask_app.sched_conf))
        algorithm.schedule_all(tasks, list(db.resources))
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

    Load the config, if necessary, and return config values.
    """
    # Set the default config values
    conf = {
        'algorithm': None,
        'default_algorithm': None,
    }

    for key in conf:
        conf[key] = bc.get('scheduler', key)
    # Set some defaults
    conf['log'] = '/'.join([bee_workdir, 'logs', 'scheduler.log'])
    conf['workdir'] = os.path.join(bee_workdir, 'scheduler')
    conf['alloc_logfile'] = os.path.join(conf['workdir'], ALLOC_LOGFILE)

    conf = argparse.Namespace(**conf)
    log.info('Config = [')
    log.info(f'\talloc_logfile = {conf.alloc_logfile}')  # noqa pylama is wrong here
    log.info(f'\talgorithm = {conf.algorithm}')
    log.info(f'\tdefault_algorithm = {conf.default_algorithm}')
    log.info(f'\tworkdir = {conf.workdir}')  # noqa
    log.info(']')
    return conf


def create_app():
    """Create the Flask app for the scheduler."""
    # TODO: Refactor this to actually create the app here
    conf = load_config_values()
    flask_app.sched_conf = conf
    # Load algorithm data
    algorithms.load(**vars(conf))

    # Create the scheduler workdir, if necessary
    # sched_listen_port = wf_utils.get_open_port()
    # wf_db.set_sched_port(sched_listen_port)
    os.makedirs(conf.workdir, exist_ok=True) # noqa
    return flask_app

# Ignore W0511: This allows us to have TODOs in the code
# pylama:ignore=W0511
