"""Tests of the TM database."""

# Disable W0621: Pylint complains about redefining 'temp_db' from the outer
#               scope. This is how pytest fixtures work.
# pylint:disable=W0621

import tempfile
import os

import pytest

from beeflow.common.db import tm_db


@pytest.fixture
def temp_db():
    """Pytest fixture for creating a temporary database."""
    fname = tempfile.mktemp()
    db = tm_db.open_db(fname)
    yield db
    os.remove(fname)


def test_empty(temp_db):
    """Test an empty database."""
    db = temp_db

    assert db.submit_queue.count() == 0
    assert db.job_queue.count() == 0


def test_push_pop(temp_db):
    """Test pushing and popping values in a database."""
    db = temp_db

    # Just push something random for the submit_queue, no need to be a real
    # task
    db.submit_queue.push(3)
    db.job_queue.push(task=45, job_id=1289, job_state='READY')

    assert db.submit_queue.count() == 1
    assert db.job_queue.count() == 1
    assert db.submit_queue.pop() == 3
    popped_job = db.job_queue.pop()
    assert popped_job.task == 45
    assert popped_job.job_id == 1289
    assert popped_job.job_state == 'READY'
    assert db.submit_queue.count() == 0
    assert db.job_queue.count() == 0


def test_push_pop_many(temp_db):
    """Test pushing and popping many values."""
    db = temp_db

    # Push 128 items
    for i in range(128):
        db.submit_queue.push(i)
        job_state = 'READY' if (i % 2) == 0 else 'COMPLETED'
        db.job_queue.push(task=i, job_id=i + 1, job_state=job_state)
        assert db.submit_queue.count() == (i + 1)
        assert db.job_queue.count() == (i + 1)
    # Now pop 128 items
    for i in range(128):
        assert db.submit_queue.pop() == i
        popped_job = db.job_queue.pop()
        assert popped_job.task == i
        assert popped_job.job_id == i + 1
        assert popped_job.job_state == 'READY' if (i % 2) == 0 else 'COMPLETED'
        assert db.submit_queue.count() == (127 - i)
        assert db.job_queue.count() == (127 - i)
    assert db.submit_queue.count() == 0
    assert db.job_queue.count() == 0


def test_clear(temp_db):
    """Test clearing the database."""
    db = temp_db

    # submit_queue
    db.submit_queue.push(3)
    db.submit_queue.push(4)
    db.submit_queue.push({123, 4, 5})
    db.submit_queue.clear()
    assert db.submit_queue.count() == 0

    # job_queue
    db.job_queue.push(task={1, 2, 3}, job_id=168, job_state='COMPLETED')
    db.job_queue.push(task={'some': 'value'}, job_id=12, job_state='READY')
    db.job_queue.push(task=(1, 2, 3), job_id=88888, job_state='FAILED')
    db.job_queue.clear()
    assert db.submit_queue.count() == 0


def test_iter(temp_db):
    """Test iterating over the values."""
    db = temp_db

    values = (127, 16)
    for val in values:
        db.submit_queue.push(val)
    for task, other in zip(db.submit_queue, values):
        assert task == other

    for val in values:
        db.job_queue.push(task=val, job_id=val, job_state='COMPLETED')
    for job, val in zip(db.job_queue, values):
        assert job.task == val
        assert job.job_id == val
        assert job.job_state == 'COMPLETED'


def test_job_queue_remove_by_id(temp_db):
    """Test removing a job by ID for the job queue."""
    db = temp_db

    db.job_queue.push(task={8, 9, 10}, job_id=888, job_state='some-state0')
    db.job_queue.push(task={10}, job_id=999, job_state='some-state1')
    db.job_queue.push(task={46, 57}, job_id=111, job_state='some-state2')

    assert db.job_queue.count() == 3

    jobs = list(db.job_queue)
    id_ = jobs[1].id
    db.job_queue.remove_by_id(id_)

    assert db.job_queue.count() == 2
    job = db.job_queue.pop()
    assert job.task == {8, 9, 10}
    assert job.job_id == 888
    assert job.job_state == 'some-state0'
    job = db.job_queue.pop()
    assert job.task == {46, 57}
    assert job.job_id == 111
    assert job.job_state == 'some-state2'
    assert db.job_queue.count() == 0


def test_job_queue_update_job_state(temp_db):
    """Test updating the job state for a job in the queue."""
    db = temp_db

    db.job_queue.push(task={8, 9, 10}, job_id='888', job_state='READY')

    jobs = list(db.job_queue)
    id_ = jobs[0].id
    db.job_queue.update_job_state(id_, 'COMPLETED')

    job = db.job_queue.pop()
    assert job.task == {8, 9, 10}
    assert job.job_id == 888
    assert job.job_state == 'COMPLETED'


def test_update_queue_empty(temp_db):
    """Test an empty update queue."""
    db = temp_db

    assert db.update_queue.updates() == []

    db.update_queue.clear()

    assert db.update_queue.updates() == []


def test_update_queue_order(temp_db):
    """Ensure that updates are returned in the correct order."""
    db = temp_db

    db.update_queue.push('wf-id', 'task-id', 'RUNNING')
    db.update_queue.push('wf-id', 'task-id', 'COMPLETED')
    db.update_queue.push('wf-id-2', 'task-id-2', 'RUNNING')
    db.update_queue.push('wf-id-2', 'task-id-2', 'FAILED')

    updates = db.update_queue.updates()
    assert updates[0].wf_id == 'wf-id'
    assert updates[0].task_id == 'task-id'
    assert updates[0].job_state == 'RUNNING'
    assert updates[1].wf_id == 'wf-id'
    assert updates[1].task_id == 'task-id'
    assert updates[1].job_state == 'COMPLETED'
    assert updates[2].wf_id == 'wf-id-2'
    assert updates[2].task_id == 'task-id-2'
    assert updates[2].job_state == 'RUNNING'
    assert updates[3].wf_id == 'wf-id-2'
    assert updates[3].task_id == 'task-id-2'
    assert updates[3].job_state == 'FAILED'

    db.update_queue.clear()
    assert db.update_queue.updates() == []
