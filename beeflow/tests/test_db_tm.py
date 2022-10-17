"""Tests of the TM database."""
import tempfile
import os

import pytest

from beeflow.common.db import tm


@pytest.fixture
def temp_db():
    """Pytest fixture for creating a temporary database."""
    fname = tempfile.mktemp()
    with tm.open_db(fname) as db:
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
    assert db.job_queue.pop() == {
        'task': 45,
        'job_id': 1289,
        'job_state': 'READY',
    }
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
        assert db.job_queue.pop() == {
            'task': i,
            'job_id': i + 1,
            'job_state': 'READY' if (i % 2) == 0 else 'COMPLETED',
        }
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

    values = (127, 16, 11999)
    for val in values:
        db.submit_queue.push(val)
    for task, other in zip(db.submit_queue, values):
        assert task == other

    for val in values:
        db.job_queue.push(task=val, job_id=val, job_state='COMPLETED')
    for job, val in zip(db.job_queue, values):
        assert 'id' in job
        assert job['task'] == val
        assert job['job_id'] == val
        assert job['job_state'] == 'COMPLETED'


def test_job_queue_remove_by_id(temp_db):
    """Test removing a job by ID for the job queue."""
    db = temp_db

    db.job_queue.push(task={8, 9, 10}, job_id=888, job_state='some-state0')
    db.job_queue.push(task={10}, job_id=999, job_state='some-state1')
    db.job_queue.push(task={46, 57}, job_id=111, job_state='some-state2')

    assert db.job_queue.count() == 3

    jobs = list(db.job_queue)
    id_ = jobs[1]['id']
    db.job_queue.remove_by_id(id_)

    assert db.job_queue.count() == 2
    job = db.job_queue.pop()
    assert job['task'] == {8, 9, 10}
    assert job['job_id'] == 888
    assert job['job_state'] == 'some-state0'
    job = db.job_queue.pop()
    assert job['task'] == {46, 57}
    assert job['job_id'] == 111
    assert job['job_state'] == 'some-state2'
    assert db.job_queue.count() == 0


def test_job_queue_update_job_state(temp_db):
    """Test updating the job state for a job in the queue."""
    db = temp_db

    db.job_queue.push(task={8, 9, 10}, job_id='888', job_state='READY')

    jobs = list(db.job_queue)
    id_ = jobs[0]['id']
    db.job_queue.update_job_state(id_, 'COMPLETED')

    job = db.job_queue.pop()
    assert job['task'] == {8, 9, 10}
    assert job['job_id'] == 888
    assert job['job_state'] == 'COMPLETED'
# Ignore W0621: PyLama complains about redefining 'temp_db' from the outer
#               scope. This is how pytest fixtures work.
# pylama:ignore=W0621
