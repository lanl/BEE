"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import requests
import subprocess
import time
import pytest


SCHEDULER_TEST_PORT = '5100'

# TODO: Job dependency tests

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
        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
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
        '--mars-task-cnt', '2', # Need 2 tasks to use MARS
        '--use-mars',
    ], shell=False)
    time.sleep(6)
    try:
        # Give control over to the test function
        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
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
        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
    finally:
        # Teardown
        # Note: Should not use proc.kill() here with flask debug
        proc.terminate()


def create_workflow(url, name, requirements):
    """Create a workflow."""
    workflow_data = {
        'requirements': requirements,
    }

    r = requests.put(f'{url}/workflows/{name}', json=workflow_data)

    assert r.ok
    return r.json()


def test_scheduler_create_workflow(scheduler):
    """Test creating a new workflow."""
    url = scheduler

    data = create_workflow(url, 'test-workflow', {})

    assert data['workflow_name'] == 'test-workflow'


def test_schedule_job_no_resources(scheduler):
    """Test scheduling a job with no resources."""
    url = scheduler
    workflow_name = 'test-workflow'
    create_workflow(url, workflow_name, {})
    task1 = {
        # 'workflow_name': workflow_name,
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    schedule = r.json()
    assert len(schedule) == 1
    alloc = schedule[task1['job_name']]
    assert not alloc['allocations']
    assert not alloc['after']


def test_schedule_job_one_resource(scheduler):
    """Test scheduling a job with one resource."""
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
    create_workflow(url, workflow_name, {})
    task1 = {
        # 'workflow_name': 'test-workflow',
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    schedule = r.json()
    alloc = schedule[task1['job_name']]
    assert len(alloc['allocations']) == 1
    assert resource1['id_'] in alloc['allocations']
    assert alloc['allocations'][resource1['id_']]['nodes'] == 1
    assert not alloc['after']


def test_schedule_job_two_resources(scheduler):
    """Test scheduling a job with two resources."""
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
    create_workflow(url, workflow_name, {})
    task1 = {
        # 'workflow_name': 'test-workflow',
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    data = r.json() 
    alloc = data[task1['job_name']]
    assert len(alloc['allocations']) == 1
    assert any(res['id_'] in alloc['allocations'] for res in (resource1, resource2))


def test_schedule_multi_job_two_resources(scheduler):
    """Test scheduling multiple jobs with two resources."""
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
    create_workflow(url, workflow_name, {})
    task1 = {
        'job_name': 'test-task-0',
        'requirements': {
            'max_runtime': 1,
        },
    }
    task2 = {
        'job_name': 'test-task-1',
        'requirements': {
            'max_runtime': 1,
        },
    }
    task3 = {
        'job_name': 'test-task-2',
        'requirements': {
            'max_runtime': 4,
            'nodes': 16,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs',
                     json=[task1, task2, task3])

    assert r.ok
    data = r.json()
    for task in (task1, task2, task3):
        alloc = data[task.job_name]
        assert any(res['id_'] in alloc['allocations'] for res in (resource1, resource2))
        # TODO: Check for proper dependencies
        assert not alloc['after']


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
    r = requests.put(f'{url}/resources', json=[resource1])

    assert r.ok
    assert r.json() == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    create_workflow(url, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1])

    assert r.ok
    schedule = r.json()
    assert len(schedule) == 1
    alloc = schedule[task1.job_name]
    assert resource1['id_'] in alloc['allocations']
    assert not alloc['after']


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
    r = requests.put(f'{url}/resources', json=[resource1])

    assert r.ok
    assert r.json() == 'created 1 resource(s)'

    workflow_name = 'test-workflow'
    create_workflow(url, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
            'nodes': 1,
        },
    }
    task2 = {
        'job_name': 'test-task-2',
        'requirements': {
            'max_runtime': 1,
            'nodes': 1,
        },
    }
    r = requests.put(f'{url}/workflows/{workflow_name}/jobs', json=[task1, task2])

    assert r.ok
    schedule = r.json()
    assert len(schedule) == 2
    # Make sure that one task is scheduled after the other
    assert (task2.job_name in schedule[task1.job_name]['after']
            or task1.job_name in schedule[task2.job_name]['after'])
    assert all(resource1['id_'] in schedule[task.job_name]['allocations']
               for task in (task1, task2))


# TODO: More job tests
# TODO: More resource tests
