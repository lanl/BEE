"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import os
import pytest
import subprocess
import time
import uuid
import requests

from beeflow.common.connection import Connection


SCHEDULER_TEST_PORT = '5100'


@pytest.fixture(scope='function')
def scheduler():
    """Fixture code to setup a new scheduler per test function.

    Start a new scheduler as a subprocess for each test function.
    """
    tmp_name = uuid.uuid4().hex
    basename = os.path.join('/tmp', tmp_name)
    socket = f'{basename}.sock'
    db = f'{basename}.db'
    env = os.environ
    # Set the DB path in the environment
    env['BEE_SCHED_DB_PATH'] = db
    # Setup
    proc = subprocess.Popen([
        'gunicorn', 'beeflow.scheduler.scheduler:create_app()', '-b', f'unix:{socket}',
    ], shell=False, env=env)
    time.sleep(2)
    try:
        # Give control over to the test function
        yield Connection(socket, prefix='bee_sched/v1')
    finally:
        # Teardown
        proc.terminate()


def test_schedule_job_no_resources(scheduler):
    """Test scheduling a job with no resources.

    Test scheduling a job with no resources.
    :param scheduler: connection returned by fixture
    :type scheduler: Connection
    """
    conn = scheduler
    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': workflow_name,
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    req = conn.put(f'workflows/{workflow_name}/jobs', json=[task1])

    print(req.text)
    assert req.ok
    data = req.json()
    assert len(data) == 1
    assert data[0]['workflow_name'] == workflow_name
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert data[0]['allocations'] == []


def test_schedule_job_one_resource(scheduler):
    """Test scheduling a job with one resource.

    Test scheduling a job with one resource.
    :param scheduler: connection returned by fixture
    :type scheduler: Connection
    """
    conn = scheduler
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    req = conn.put('resources', json=[resource1])

    assert req.ok
    assert req.json() == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    req = conn.put(f'workflows/{workflow_name}/jobs', json=[task1])

    assert req.ok
    data = req.json()
    assert len(data) == 1
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) == 1
    assert data[0]['allocations'][0]['id_'] == 'resource-1'
    assert data[0]['allocations'][0]['nodes'] == 1
    assert data[0]['allocations'][0]['start_time'] == 0
    assert data[0]['allocations'][0]['max_runtime'] == 1


def test_schedule_job_two_resources(scheduler):
    """Test scheduling a job with two resources.

    Test scheduling a job with two resources.
    :param scheduler: connection returned by fixture
    :type scheduler: Connection
    """
    conn = scheduler
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    resource2 = {
        'id_': 'resource-2',
        'nodes': 64,
    }
    req = conn.put('resources', json=[resource1, resource2])

    assert req.ok
    assert req.json() == 'created 2 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    req = conn.put(f'workflows/{workflow_name}/jobs', json=[task1])

    assert req.ok
    data = req.json()
    assert len(data) == 1
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0


def test_schedule_multi_job_two_resources(scheduler):
    """Test scheduling multiple jobs with two resources.

    Test scheduling multiple jobs with two resources.
    :param scheduler: connection returned by fixture
    :type scheduler: Connection
    """
    conn = scheduler
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-0',
        'nodes': 10,
    }
    resource2 = {
        'id_': 'resource-1',
        'nodes': 16,
    }
    req = conn.put('resources', json=[resource1, resource2])

    assert req.ok
    assert req.json() == 'created 2 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task-0',
        'requirements': {
            'max_runtime': 1,
        },
    }
    task2 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task-1',
        'requirements': {
            'max_runtime': 1,
        },
    }
    task3 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task-2',
        'requirements': {
            'max_runtime': 4,
            'nodes': 16,
        },
    }
    req = conn.put(f'workflows/{workflow_name}/jobs',
                   json=[task1, task2, task3])

    assert req.ok
    data = req.json()
    assert len(data) == 3
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task-0'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0
    # Ensure proper scheduled time
    assert data[0]['allocations'][0]['start_time'] < 6
    assert data[1]['workflow_name'] == 'test-workflow'
    assert data[1]['task_name'] == 'test-task-1'
    assert data[1]['requirements']['max_runtime'] == 1
    assert len(data[1]['allocations']) > 0
    # Ensure proper scheduled time
    assert data[1]['allocations'][0]['start_time'] < 6
    assert data[2]['workflow_name'] == 'test-workflow'
    assert data[2]['task_name'] == 'test-task-2'
    assert data[2]['requirements']['max_runtime'] == 4
    assert data[2]['requirements']['nodes'] == 16
    assert len(data[2]['allocations']) > 0
    # Ensure proper scheduled time
    assert data[2]['allocations'][0]['start_time'] < 6


# Ignore R1732: This suggestion about using `with` doesn't apply here.
# Ignore W0621: These are fixtures; it's supposed to work this way.
# pylama:ignore=R1732,W0621
