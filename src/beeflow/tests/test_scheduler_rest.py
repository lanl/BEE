"""Scheduler REST test cases.

Tests of the REST interface for BEE Scheduler.
"""
import requests
import subprocess
import time
import flask
import pytest

import beeflow.scheduler.scheduler as scheduler
#import beeflow.scheduler.db as db


class MockDB:
    """Mock database class for testing."""

    def __init__(self):
        """Mock database constructor."""
        # TODO


@pytest.fixture
def scheduler_client():
    """Fixture for setting up the scheduler client."""
    app = scheduler.flask_app
    app.testing = True

    with app.app_context():
        # db.setup_db(app)
        flask.g.db = MockDB()
        with app.test_client() as client:
            yield client
    #with app.app_context():
    #    db.set_interface(MockDB())


SCHEDULER_TEST_PORT = '5100'
BASE_URL = '/bee_sched/v1'

# TODO: Job dependency tests

#@pytest.fixture(scope='function')
#def scheduler():
#    """Fixture code to setup a new scheduler per test function.
#
#    Start a new scheduler as a subprocess for each test function.
#    """
#    # Setup
#    proc = subprocess.Popen([
#        'python', '-m', 'beeflow.scheduler.scheduler',
#        '-p', SCHEDULER_TEST_PORT,
#        '--no-config',
#        '--log', '/tmp/sched.log',
#        # '--use-mars',  # Required for testing MARS
#    ], shell=False)
#    time.sleep(6)
#    try:
#        # Give control over to the test function
#        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
#    finally:
#        # Teardown
#        # Note: Should not use proc.kill() here with flask debug
#        proc.terminate()
#
#@pytest.fixture(scope='function')
#def scheduler_mars_simple():
#    """Fixture code to setup a new MARS + Simple algorithm scheduler.
#
#    Start a new scheduler as a subprocess for each test function.
#    """
#    # Setup
#    proc = subprocess.Popen([
#        'python', 'beeflow/scheduler/scheduler.py',
#        '-p', SCHEDULER_TEST_PORT,
#        '--no-config',
#        '--log', '/tmp/sched.log',
#        '--mars-task-cnt', '2', # Need 2 tasks to use MARS
#        '--use-mars',
#    ], shell=False)
#    time.sleep(6)
#    try:
#        # Give control over to the test function
#        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
#    finally:
#        # Teardown
#        # Note: Should not use proc.kill() here with flask debug
#        proc.terminate()
#
#@pytest.fixture(scope='function')
#def scheduler_mars():
#    """Fixture code to setup a new MARS scheduler per test function.
#
#    Start a new MARS scheduler as a subprocess for each test function.
#    """
#    # Setup
#    proc = subprocess.Popen([
#        'python', 'beeflow/scheduler/scheduler.py',
#        '-p', SCHEDULER_TEST_PORT,
#        '--no-config',
#        '--log', '/tmp/sched.log',
#        '--algorithm', 'mars',  # Test only MARS
#    ], shell=False)
#    time.sleep(6)
#    try:
#        # Give control over to the test function
#        yield 'http://localhost:%s/bee_sched/v1' % SCHEDULER_TEST_PORT
#    finally:
#        # Teardown
#        # Note: Should not use proc.kill() here with flask debug
#        proc.terminate()


def create_workflow(client, name, requirements):
    """Create a workflow."""
    workflow_data = {
        'requirements': requirements,
    }

    resp = client.put(f'{BASE_URL}/workflows/{name}', json=workflow_data)
    # print(resp)

    # assert r.ok
    assert resp.status_code == 201
    return resp.get_json()


def create_resources(client, resources):
    """Create a list of resources."""
    resp = client.put(f'{BASE_URL}/resources', json=resources)

    # assert r.ok
    assert resp.status_code == 201
    assert resp.json() == f'created {count} resource(s)'


def schedule_tasks(client, workflow_name, tasks):
    """Schedule tasks and return the schedule."""
    resp = client.put(f'{BASE_URL}/workflows/{workflow_name}/jobs', json=tasks)

    # assert r.ok
    assert resp.status_code == 200
    return r.json()


def test_scheduler_create_workflow(scheduler_client):
    """Test creating a new workflow."""
    # url = scheduler
    client = scheduler_client

    data = create_workflow(client, 'test-workflow', {})

    assert data['workflow_name'] == 'test-workflow'


def test_schedule_job_no_resources(scheduler_client):
    """Test scheduling a job with no resources."""
    # url = scheduler
    client = scheduler_client
    workflow_name = 'test-workflow'
    create_workflow(client, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    schedule = schedule_tasks(client, workflow_name, [task1])

    assert len(schedule) == 1
    alloc = schedule[task1['job_name']]
    assert not alloc['allocations']
    assert not alloc['after']


def test_schedule_job_one_resource(scheduler_client):
    """Test scheduling a job with one resource."""
    # url = scheduler
    client = scheduler_client
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    create_resources(client, [resource1])

    workflow_name = 'test-workflow'
    create_workflow(client, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    schedule = schedule_tasks(client, workflow_name, [task1])

    alloc = schedule[task1['job_name']]
    assert len(alloc['allocations']) == 1
    assert resource1['id_'] in alloc['allocations']
    assert alloc['allocations'][resource1['id_']]['nodes'] == 1
    assert not alloc['after']


def test_schedule_job_two_resources(scheduler_client):
    """Test scheduling a job with two resources."""
    # url = scheduler
    client = scheduler_client
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    resource2 = {
        'id_': 'resource-2',
        'nodes': 64,
    }
    create_resources(client, [resource1, resource2])

    workflow_name = 'test-workflow'
    create_workflow(client, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    schedule = schedule_tasks(client, workflow_name, [task1])

    alloc = schedule[task1['job_name']]
    assert len(alloc['allocations']) == 1
    assert any(res['id_'] in alloc['allocations'] for res in (resource1, resource2))


def test_schedule_multi_job_two_resources(scheduler_client):
    """Test scheduling multiple jobs with two resources."""
    # url = scheduler
    client = scheduler_client
    # Create a single resource
    resource1 = {
        'id_': 'resource-0',
        'nodes': 10,
    }
    resource2 = {
        'id_': 'resource-1',
        'nodes': 16,
    }

    create_resources(client, [resource1, resource2])

    workflow_name = 'test-workflow'
    create_workflow(client, workflow_name, {})
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
    schedule = schedule_tasks(client, workflow_name, [task1, task2, task3])

    for task in (task1, task2, task3):
        alloc = schedule[task.job_name]
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
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 10,
    }
    create_resources(url, [resource1])

    workflow_name = 'test-workflow'
    create_workflow(url, workflow_name, {})
    task1 = {
        'job_name': 'test-task',
        'requirements': {
            'max_runtime': 1,
        },
    }
    schedule = schedule_tasks(url, workflow_name, [task1])

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
    # Create a single resource
    resource1 = {
        'id_': 'resource-1',
        'nodes': 1,
    }
    create_resources(url, [resource1])

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
    schedule = schedule_tasks(url, workflow_name, [task1, task2])

    assert len(schedule) == 2
    # Make sure that one task is scheduled after the other
    assert (task2.job_name in schedule[task1.job_name]['after']
            or task1.job_name in schedule[task2.job_name]['after'])
    assert all(resource1['id_'] in schedule[task.job_name]['allocations']
               for task in (task1, task2))


def test_schedule_two_dependent_tasks(scheduler_client):
    """Test scheduling two tasks with dependencies."""
    # url = scheduler
    client = scheduler_client
    resources = [
        {
            'id_': 'resource-0',
            'nodes': 1,
        },
    ]
    resources = create_resources(client, resources)

    workflow_name = 'test-dep-workflow'
    create_workflow(client, workflow_name, {})

    task1 = {
        'job_name': 'task-1',
        'requirements': {
            'nodes': 1,
        },
    }
    # task-2 depends on task-1
    task2 = {
        'job_name': 'task-2',
        'requirements': {
            'nodes': 1,
        },
        'dep': ['task-1']
    }

    schedule = schedule_tasks(client, workflow_name, [task1, task2])

    alloc = schedule[task1['job_name']]
    assert resources[0]['id_'] in alloc['allocations']
    assert not alloc['after']
    alloc = schedule[task2['job_name']]
    assert resources[0]['id_'] in alloc['allocations']
    # assert len(alloc['after']) == 1
    assert alloc['after'] == [task1['job_name']]


# TODO: More job tests
# TODO: More resource tests
