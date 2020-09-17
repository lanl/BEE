"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import requests
import subprocess
import time
import pytest


SCHEDULER_TEST_PORT = '5100'


# @contextlib.contextmanager
@pytest.fixture(scope='function')
def scheduler():
    """Fixture code to setup a new scheduler per test function.

    Start a new scheduler as a subprocess for each test function.
    """
    # Setup
    proc = subprocess.Popen([
        'python', 'beeflow/scheduler/scheduler.py',
        '-p', SCHEDULER_TEST_PORT,
        '--no-config',
        '--use-mars',  # Required for testing MARS
    ], shell=False)
    time.sleep(2)
    try:
        # Give control over to the test function
        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
    finally:
        # Teardown
        # Note: Should not use proc.kill() here with flask debug
        proc.terminate()


def test_schedule_job_no_resources(scheduler):
    """Test scheduling a job with no resources.

    Test scheduling a job with no resources.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler
    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': workflow_name,
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    data = r.json()
    assert len(data) == 1
    assert data[0]['workflow_name'] == workflow_name
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert data[0]['allocations'] == []


def test_schedule_job_one_resource(scheduler):
    """Test scheduling a job with one resource.

    Test scheduling a job with one resource.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    r = requests.put(f'{url}/resources', json=[resource1])

    assert r.ok
    assert r.json() == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    data = r.json()
    assert len(data) == 1
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) == 1
    assert data[0]['allocations'][0]['id_'] == 'resource-1'
    assert data[0]['allocations'][0]['nodes'] == 1
    assert data[0]['allocations'][0]['start_time'] == int(time.time())
    assert data[0]['allocations'][0]['max_runtime'] == 1


def test_schedule_job_two_resources(scheduler):
    """Test scheduling a job with two resources.

    Test scheduling a job with two resources.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler
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
    r = requests.put(f'{url}/resources', json=[resource1, resource2])

    assert r.ok
    assert r.json() == 'created 2 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    data = r.json() 
    assert len(data) == 1
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0


def test_schedule_multi_job_two_resources(scheduler):
    """Test scheduling multiple jobs with two resources.

    Test scheduling multiple jobs with two resources.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler
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
    r = requests.put(f'{url}/resources', json=[resource1, resource2])

    assert r.ok
    assert r.json() == 'created 2 resource(s)'

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
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs',
                     json=[task1, task2, task3])

    assert r.ok
    data = r.json()
    assert len(data) == 3
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] == 'test-task-0'
    assert data[0]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0
    assert data[1]['workflow_name'] == 'test-workflow'
    assert data[1]['task_name'] == 'test-task-1'
    assert data[1]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0
    assert data[2]['workflow_name'] == 'test-workflow'
    assert data[2]['task_name'] == 'test-task-2'
    assert data[2]['requirements']['max_runtime'] == 4
    assert data[2]['requirements']['nodes'] == 16
    assert len(data[2]['allocations']) > 0
# TODO: More job tests
# TODO: More resource tests
