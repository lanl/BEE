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
from beeflow.common.db import sched
from beeflow.common import log as bee_logging


log = bee_logging.setup(__name__)

flask_app = Flask(__name__)
api = Api(flask_app)

# We have to call bc.init() here due to how gunicorn works
bc.init()


def get_db_path():
    """Get the database path."""
    # Favor the environment variable if it exists
    path = os.getenv('BEE_SCHED_DB_PATH')
    if path is None:
        workdir = bc.get('DEFAULT', 'bee_workdir')
        path = os.path.join(workdir, 'sched.db')
    return path


def connect_db(fn):
    """Decorate a function for connecting to a database."""
    def wrap(*pargs, **kwargs):
        """Decorate the function."""
        with sched.open_db(get_db_path()) as db:
            return fn(db, *pargs, **kwargs)

    return wrap


class ResourcesHandler(Resource):
    """Resources handler."""

    @staticmethod
    @connect_db
    def put(db):
        """Create a list of resources to use for allocation."""
        db.resources.clear()
        resources = [resource_allocation.Resource.decode(r)
                     for r in request.json]
        db.resources.extend(resources)
        return f'created {len(resources)} resource(s)'

    @staticmethod
    @connect_db
    def get(db):
        """Get a list of all resources."""
        return [r.encode() for r in db.resources]


class WorkflowJobHandler(Resource):
    """Schedule jobs for a specific workflow with the current resources."""

    @staticmethod
    @connect_db
    def put(db, workflow_name):  # noqa ('workflow_name' may be used in the future)
        """Schedules a new list of independent tasks with available resources."""
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
        'log': None,
        'alloc_logfile': None,
        'algorithm': None,
        'default_algorithm': None,
        'workdir': None,
    }

    for key in conf:
        conf[key] = bc.get('scheduler', key)
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    # Set some defaults
    if not conf['log']:
        conf['log'] = '/'.join([bee_workdir, 'logs', 'scheduler.log'])
    if not conf['workdir']:
        conf['workdir'] = os.path.join(bee_workdir, 'scheduler')
    if not conf['alloc_logfile']:
        conf['alloc_logfile'] = os.path.join(conf['workdir'],
                                             ALLOC_LOGFILE)

    conf = argparse.Namespace(**conf)
    log.info('Config = [')
    log.info(f'\talloc_logfile = {conf.alloc_logfile}')
    log.info(f'\talgorithm = {conf.algorithm}')
    log.info(f'\tdefault_algorithm = {conf.default_algorithm}')
    log.info(f'\tworkdir = {conf.workdir}')
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
    os.makedirs(conf.workdir, exist_ok=True)
    return flask_app

# Ignore todo's or pylama fails
# pylama:ignore=W0511
