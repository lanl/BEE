"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import os
import tempfile
import pytest

from beeflow.scheduler.scheduler import create_app

SCHEDULER_TEST_PORT = '5100'


def endpoint(*pargs):
    """Return the endpoint url for a resource."""
    return '/'.join(['bee_sched/v1', *pargs])


@pytest.fixture(scope='function')
def scheduler(mocker):
    """Fixture code to setup a new scheduler per test function.

    Start a new scheduler as a subprocess for each test function.
    """
    app = create_app()
    app.config.update({
        'TESTING': True,
    })
    fname = tempfile.mktemp(suffix='.db')
    mocker.patch('beeflow.scheduler.scheduler.db_path', fname)
    yield app.test_client()
    os.remove(fname)


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
    req = conn.put(endpoint('workflows', workflow_name, 'jobs'), json=[task1])

    assert req.status_code == 200
    data = req.json
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
    req = conn.put(endpoint('resources'), json=[resource1])

    assert req.status_code == 200
    assert req.json == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    req = conn.put(endpoint('workflows', workflow_name, 'jobs'), json=[task1])

    assert req.status_code == 200
    data = req.json
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
    req = conn.put(endpoint('resources'), json=[resource1, resource2])

    assert req.status_code == 200
    assert req.json == 'created 2 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    req = conn.put(endpoint('workflows', workflow_name, 'jobs'), json=[task1])

    assert req.status_code == 200
    data = req.json
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
    req = conn.put(endpoint('resources'), json=[resource1, resource2])

    assert req.status_code == 200
    assert req.json == 'created 2 resource(s)'

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
    req = conn.put(endpoint('workflows', workflow_name, 'jobs'),
                   json=[task1, task2, task3])

    assert req.status_code == 200
    data = req.json
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
