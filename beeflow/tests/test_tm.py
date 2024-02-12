"""Unit tests for the task manager."""

import tempfile
import os
import uuid
import pytest
import jsonpickle
from mocks import mock_put
from mocks import MockWorkerCompletion, MockWorkerSubmission

from beeflow.common.db.bdb import connect_db
from beeflow.common.db import tm_db
import beeflow.task_manager.task_manager as tm
from beeflow.common.wf_data import Task
import beeflow


@pytest.fixture
def flask_client():
    """Client lets us run flask queries."""
    app = tm.create_app()
    client = app.test_client()
    yield client


def generate_tasks(n):
    """Generate n tasks for testing."""
    return [
        Task(f'task-{i}', base_command=['ls', '/'], hints=[], requirements=[],
             inputs=[], outputs=[], stdout=None, stderr=None,
             workflow_id=uuid.uuid4().hex)
        for i in range(n)
    ]


@pytest.fixture
def temp_db():
    """Pytest fixture for creating a temporary database."""
    fname = tempfile.mktemp(suffix='.db')
    db = connect_db(tm_db, fname)
    yield db
    os.remove(fname)


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_submit_task(flask_client, mocker, temp_db):  # noqa
    """Create a workflow and get the ID back."""
    mocker.patch('beeflow.task_manager.utils.worker_interface',
                 MockWorkerSubmission)
    mocker.patch('beeflow.task_manager.utils.db_path', lambda: temp_db.db_file)
    # Generate a task
    tasks = generate_tasks(1)
    tasks_json = jsonpickle.encode(tasks)

    response = flask_client.post('/bee_tm/v1/task/submit/',
                                 json={'tasks': tasks_json})

    mocker.patch('beeflow.task_manager.utils.worker_interface',
                 MockWorkerSubmission)

    # Patch the connection object for WFM communication
    mocker.patch('beeflow.common.connection.Connection.put', mock_put)
    beeflow.task_manager.background.process_queues()

    msg = response.get_json()['msg']
    status = response.status_code
    job_queue = list(temp_db.job_queue)

    # We should only have a single job on the queue
    assert len(job_queue) == 1
    job = job_queue[0]
    assert job.task == tasks[0]
    assert job.job_id == 1
    assert job.job_state == 'RUNNING'

    assert status == 200
    assert msg == 'Tasks Added!'


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_completed_task(flask_client, mocker, temp_db): # noqa
    """Tests how the task manager processes a completed task."""
    # 42 is the sample task ID
    mocker.patch('beeflow.task_manager.utils.worker_interface',
                 MockWorkerCompletion)
    # Patch the connection object for WFM communication
    mocker.patch('beeflow.common.connection.Connection.put', mock_put)
    mocker.patch('beeflow.task_manager.utils.db_path', lambda: temp_db.db_file)

    # This should notice the job is complete and empty the job_queue
    beeflow.task_manager.background.process_queues()
    job_queue = list(temp_db.job_queue)
    assert len(job_queue) == 0


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_remove_task(flask_client, mocker, temp_db):  # noqa
    """Test cancelling a workflow and removing tasks."""
    task1, task2, task3 = generate_tasks(3)
    # Add a few tasks
    temp_db.job_queue.push(task=task1, job_id=1, job_state='RUNNING')
    temp_db.job_queue.push(task=task2, job_id=2, job_state='PENDING')
    temp_db.job_queue.push(task=task3, job_id=3, job_state='PENDING')

    mocker.patch('beeflow.task_manager.utils.worker_interface',
                 MockWorkerCompletion)
    mocker.patch('beeflow.task_manager.utils.db_path', lambda: temp_db.db_file)

    response = flask_client.delete('/bee_tm/v1/task/')

    msg = response.get_json()['msg']
    status = response.status_code
    assert status == 200
    assert msg.count('CANCELLED') == 3
