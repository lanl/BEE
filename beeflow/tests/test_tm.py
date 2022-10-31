"""This is a sample docstring."""

import uuid
import os
import pytest
import jsonpickle
from mocks import MockWorkerCompletion, MockWorkerSubmission
from mocks import mock_put

import beeflow.task_manager as tm
from beeflow.common.wf_data import Task
import beeflow


@pytest.fixture
def flask_client():
    """Client lets us run flask queries."""
    app = tm.flask_app
    app.config['TESTING'] = True
    db_path = f'/tmp/{uuid.uuid4().hex}.db'
    app.config['TESTING_DB_PATH'] = db_path
    client = app.test_client()
    yield client
    os.remove(db_path)


@pytest.fixture
@tm.connect_db
def database(db):
    """Fixture for connecting to the TM DB."""
    return db


def generate_tasks(n):
    """Generate n tasks for testing."""
    return [
        Task(f'task-{i}', base_command=['ls', '/'], hints=[], requirements=[],
             inputs=[], outputs=[], stdout=None, stderr=None,
             workflow_id=uuid.uuid4().hex)
        for i in range(n)
    ]


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_submit_task(flask_client, mocker, database):  # noqa
    """Create a workflow and get the ID back."""
    # Generate a task
    tasks = generate_tasks(1)
    tasks_json = jsonpickle.encode(tasks)

    response = flask_client.post('/bee_tm/v1/task/submit/',
                                 json={'tasks': tasks_json})

    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerSubmission)

    # Patch the connection object for WFM communication
    mocker.patch('beeflow.common.connection.Connection.put', mock_put)
    beeflow.task_manager.process_queues()

    msg = response.get_json()['msg']
    status = response.status_code

    job_queue = list(database.job_queue)

    # We should only have a single job on the queue
    assert len(job_queue) == 1
    job = job_queue[0]
    assert job['task'] == tasks[0]
    assert job['job_id'] == 1
    assert job['job_state'] == 'RUNNING'

    assert status == 200
    assert msg == 'Tasks Added!'


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_completed_task(flask_client, mocker, database): # noqa
    """Tests how the task manager processes a completed task."""
    # 42 is the sample task ID
    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerCompletion)
    # Patch the connection object for WFM communication
    mocker.patch('beeflow.common.connection.Connection.put', mock_put)

    # This should notice the job is complete and empty the job_queue
    beeflow.task_manager.process_queues()
    job_queue = list(database.job_queue)
    assert len(job_queue) == 0


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_remove_task(flask_client, mocker, database):  # noqa
    """Test cancelling a workflow and removing tasks."""
    task1, task2, task3 = generate_tasks(3)
    # Add a few tasks
    database.job_queue.push(task=task1, job_id=1, job_state='RUNNING')
    database.job_queue.push(task=task2, job_id=2, job_state='PENDING')
    database.job_queue.push(task=task3, job_id=3, job_state='PENDING')

    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerCompletion)

    response = flask_client.delete('/bee_tm/v1/task/')

    msg = response.get_json()['msg']
    print(msg)
    status = response.status_code
    assert status == 200
    assert msg.count('CANCELLED') == 3
