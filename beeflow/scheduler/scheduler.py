#!/usr/bin/env python3
"""REST Interface for the BEE Scheduler."""

import argparse
import sys
import logging
import os

from flask import Flask, request
from flask_restful import Resource, Api

from beeflow.scheduler import algorithms
from beeflow.scheduler import task
from beeflow.scheduler import resource_allocation
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.log import main_log as log
from beeflow.common.db import sched
import beeflow.common.log as bee_logging

sys.excepthook = bee_logging.catch_exception

flask_app = Flask(__name__)
api = Api(flask_app)

# We have to call bc.init() here due to how gunicorn works
bc.init()


def connect_db(fn):
    """Decorate a function for connecting to a database."""
    workdir = bc.get('DEFAULT', 'bee_workdir')
    path = os.path.join(workdir, 'sched.db')

    def wrap(*pargs, **kwargs):
        """Decorate the function."""
        with sched.open_db(path) as db:
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
    def put(db, workflow_name):
        """Schedules a new list of independent tasks with available resources."""
        print('Scheduling', workflow_name)
        data = request.json
        tasks = [task.Task.decode(t) for t in data]
        # Pick the scheduling algorithm
        algorithm = algorithms.choose(tasks, **vars(flask_app.sched_conf))
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
        'use_mars': False,
        'mars_model': MODEL_FILE,
        'mars_task_cnt': MARS_CNT,
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
    log.info(f'\tuse_mars = {conf.use_mars}')
    log.info(f'\tmars_model = {conf.mars_model}')
    log.info(f'\tmars_task_cnt = {conf.mars_task_cnt}')
    log.info(f'\talloc_logfile = {conf.alloc_logfile}')
    log.info(f'\talgorithm = {conf.algorithm}')
    log.info(f'\tdefault_algorithm = {conf.default_algorithm}')
    log.info(f'\tworkdir = {conf.workdir}')
    log.info(']')
    return conf


def create_app():
    """Create the Flask app for the scheduler."""
    # TODO: Refactor this to actually create the app here
    CONF = load_config_values()
    workdir = bc.get('DEFAULT', 'bee_workdir')
    handler = bee_logging.save_log(bee_workdir=workdir, log=log, logfile='scheduler.log')
    flask_app.sched_conf = CONF
    # Load algorithm data
    algorithms.load(**vars(CONF))

    # Create the scheduler workdir, if necessary
    os.makedirs(CONF.workdir, exist_ok=True)
    return flask_app

# Ignore todo's or pylama fails
# pylama:ignore=W0511
