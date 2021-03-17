
"""Test the SimpleWorker class."""

import time

import beeflow.common.worker.simple_worker as simple_worker
# import beeflow.tests.mocks as mocks
import beeflow.common.wf_data as wf_data


def test_simple_worker_submit_task_cancel_task():
    """Test submitting a simple task and then cancelling it."""
    worker = simple_worker.SimpleWorker()
    # TODO: Add a sleep command for this task
    # task = mocks.MockTask('test-task')
    task = wf_data.Task('test-task', command='sleep 100', hints={},
                        subworkflow='', inputs=set(), outputs=set())

    id_, state0 = worker.submit_task(task)
    state1 = worker.cancel_task(id_)

    # Ensure we have a valid ID and state
    assert id_ >= 0
    assert state0 == 'PENDING'
    assert state1 == 'CANCELLED'


def test_simple_worker_submit_task_query_task_cancel_task():
    """Test submitting a simple task and then cancelling it."""
    worker = simple_worker.SimpleWorker()
    # TODO: Add a sleep command for this task
    # task = mocks.MockTask('test-task')
    task = wf_data.Task('test-task', command='sleep 100', hints={},
                        subworkflow='', inputs=set(), outputs=set())

    id_, state0 = worker.submit_task(task)
    state1 = worker.query_task(id_)
    state2 = worker.cancel_task(id_)

    # Ensure we have a valid ID and state
    assert id_ >= 0
    assert state0 == 'PENDING'
    assert state1 == 'RUNNING'
    assert state2 == 'CANCELLED'


def test_simple_worker_submit_task_wait_complete():
    """Test submitting a simple task and then waiting for it to complete."""
    worker = simple_worker.SimpleWorker()
    task = wf_data.Task('test-task', command='sleep 3', hints={},
                        subworkflow='', inputs=set(), outputs=set())

    id_, state0 = worker.submit_task(task)

    time.sleep(1)
    state = worker.query_task(id_)
    while state != 'COMPLETED':
        assert state == 'PENDING' or state == 'RUNNING'
        time.sleep(1)
        state = worker.query_task(id_)
    assert state == 'COMPLETED'

# TODO: Add tests for container runtimes
