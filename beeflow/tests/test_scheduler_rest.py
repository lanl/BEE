"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import subprocess
import time
import requests
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
        'python', '-m', 'beeflow.scheduler.scheduler',
        '-p', SCHEDULER_TEST_PORT,
        '--no-config',
        '--log', '/tmp/sched.log',
        # '--use-mars',  # Required for testing MARS
    ], shell=False)
    time.sleep(6)
    try:
        # Give control over to the test function
        yield f'http://localhost:{SCHEDULER_TEST_PORT}/bee_sched/v1'
    finally:
        # Teardown
        # Note: Should not use proc.kill() here with flask debug
        proc.terminate()


@pytest.fixture(scope='function')
def scheduler_mars_simple():
    """Fixture code to setup a new MARS + Simple algorithm scheduler.

    Start a new scheduler as a subprocess for each test function.
    """
    # Setup
    proc = subprocess.Popen([
        'python', 'beeflow/scheduler/scheduler.py',
        '-p', SCHEDULER_TEST_PORT,
        '--no-config',
        '--log', '/tmp/sched.log',
        '--mars-task-cnt', '2',  # Need 2 tasks to use MARS
        '--use-mars',
    ], shell=False)
    time.sleep(6)
    try:
        # Give control over to the test function
        yield f'http://localhost:{SCHEDULER_TEST_PORT}/bee_sched/v1'
    finally:
        # Teardown
        # Note: Should not use proc.kill() here with flask debug
        proc.terminate()


@pytest.fixture(scope='function')
def scheduler_mars():
    """Fixture code to setup a new MARS scheduler per test function.

    Start a new MARS scheduler as a subprocess for each test function.
    """
    # Setup
    proc = subprocess.Popen([
        'python', 'beeflow/scheduler/scheduler.py',
        '-p', SCHEDULER_TEST_PORT,
        '--no-config',
        '--log', '/tmp/sched.log',
        '--algorithm', 'mars',  # Test only MARS
    ], shell=False)
    time.sleep(6)
    try:
        # Give control over to the test function
        yield f'http://localhost:{SCHEDULER_TEST_PORT}/bee_sched/v1'
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
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

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
    req = requests.put(f'{url}/resources', json=[resource1])

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
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

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
    req = requests.put(f'{url}/resources', json=[resource1, resource2])

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
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

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
    req = requests.put(f'{url}/resources', json=[resource1, resource2])

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
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs',
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


def test_schedule_one_job_one_resource_mars_simple(scheduler_mars_simple):
    """Test scheduling a job with one task.

    Test scheduling a job with one resource. Here the MARS + Simple scheduler
    should use a simple algorithm (not MARS) to schedule the task since we
    only have one to schedule.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler_mars_simple
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    req = requests.put(f'{url}/resources', json=[resource1])

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
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

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


def test_schedule_two_jobs_one_resource_mars_simple(scheduler_mars_simple):
    """Test scheduling a job with two tasks.

    Test scheduling a job with two resources. Here the MARS + Simple scheduler
    should use MARS for scheduling since we have two tasks.
    :param scheduler: url returned by scheduler fixture function
    :type scheduler: str
    """
    url = scheduler_mars_simple
    # with scheduler() as url:
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 1,
    }
    req = requests.put(f'{url}/resources', json=[resource1])

    assert req.ok
    assert req.json() == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    task1 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
            'nodes': 1,
        },
    }
    task2 = {
        'workflow_name': 'test-workflow',
        'task_name': 'test-task-2',
        'requirements': {
            'max_runtime': 1,
            'nodes': 1,
        },
    }
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1, task2])

    assert req.ok
    data = req.json()
    assert len(data) == 2
    assert data[0]['workflow_name'] == 'test-workflow'
    assert data[1]['workflow_name'] == 'test-workflow'
    assert data[0]['task_name'] != data[1]['task_name']
    assert data[0]['requirements']['max_runtime'] == 1
    assert data[1]['requirements']['max_runtime'] == 1
    assert len(data[0]['allocations']) > 0
    assert len(data[1]['allocations']) > 0
    # Make sure that one task is scheduled after the other
    assert (data[0]['allocations'][0]['start_time']
            == (data[1]['allocations'][0]['start_time'] - 1)
            or data[1]['allocations'][0]['start_time']
            == (data[0]['allocations'][0]['start_time'] - 1))


def test_mars_timing(scheduler_mars):
    """Test that the scheduler uses 0 based timing.

    Test that the scheduler uses 0 based timing and not UNIX timestamp
    scheduling.
    """
    url = scheduler_mars
    resources = [
        {
            "id_": "0",
            "nodes": 1,
        },
        {
            "id_": "1",
            "nodes": 1,
        },
        {
            "id_": "2",
            "nodes": 1,
        },
        {
            "id_": "3",
            "nodes": 1,
        },
    ]
    req = requests.put(f'{url}/resources', json=resources)

    assert req.ok
    assert req.json() == 'created 4 resource(s)'

    workflow_name = 'workflow'
    tasks = [
        {
            "workflow_name": "workflow",
            "task_name": "0",
            "requirements": {
                "max_runtime": 1,
                "nodes": 1,
            }
        },
        {
            "workflow_name": "workflow",
            "task_name": "1",
            "requirements": {
                "max_runtime": 1,
                "nodes": 1,
            }
        },
    ]
    req = requests.put(f'{url}/workflows/{workflow_name}/jobs',
                       json=tasks)

    assert req.ok
    data = req.json()
    # Ensure both start times are good (much less than time.time())
    assert data[0]['allocations'][0]['start_time'] < (time.time() / 8)
    assert data[1]['allocations'][0]['start_time'] < (time.time() / 8)

# Ignore R1732: This suggestion about using `with` doesn't apply here.
# Ignore W0621: These are fixtures; it's supposed to work this way.
# pylama:ignore=R1732,W0621
