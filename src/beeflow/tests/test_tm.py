"""This is a sample docstring."""

import pytest
import jsonpickle
import requests
from mocks import MockWFI, MockWorkerCompletion, MockWorkerSubmission
from mocks import mock_put

import beeflow.task_manager as tm
import beeflow


@pytest.fixture
def flask_client():
    """Client lets us run flask queries."""
    app = tm.flask_app
    app.config['TESTING'] = True
    client = app.test_client()
    return client


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_submit_task(flask_client, mocker):  # noqa
    """Create a workflow and get the ID back."""
    wfi = MockWFI()
    task = list(wfi.get_dependent_tasks(wfi.get_task_by_id(0)))[0]
    task_json = jsonpickle.encode(task)

    response = flask_client.post('/bee_tm/v1/task/submit/',
                                 json={'task': task_json})

    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerSubmission)

    mocker.patch.object(requests, 'put', side_effect=mock_put)
    beeflow.task_manager.process_queues()

    msg = response.get_json()['msg']
    status = response.status_code

    job_queue = beeflow.task_manager.job_queue
    # 42 is the sample task ID
    job = job_queue[0][42]

    # We should only have a single job on the queue
    assert len(job_queue) == 1
    assert job['name'] == 'task'
    assert job['job_id'] == 1
    assert job['job_state'] == 'RUNNING'

    assert status == 200
    assert msg == 'Task Added!'


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_completed_task(flask_client, mocker): # noqa
    """Tests how the task manager processes a completed task."""
    job_queue = beeflow.task_manager.job_queue
    # 42 is the sample task ID
    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerCompletion)
    mocker.patch.object(requests, 'put', side_effect=mock_put)

    # This should notice the job is complete and empty the job_queue
    beeflow.task_manager.process_queues()
    assert len(job_queue) == 0


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_remove_task(flask_client, mocker):  # noqa
    """Test cancelling a workflow and removing tasks."""
    # Add a few tasks
    beeflow.task_manager.job_queue.append({2: {'name': 'task1',
                                               'job_id': 1,
                                               'job_state':
                                               'RUNNING'}
                                           })

    beeflow.task_manager.job_queue.append({4: {'name': 'task2',
                                               'job_id': 2,
                                               'job_state':
                                               'PENDING'}
                                           })

    beeflow.task_manager.job_queue.append({6: {'name': 'task3',
                                               'job_id': 3,
                                               'job_state':
                                               'PENDING'}
                                           })

    mocker.patch('beeflow.task_manager.worker',
                 new_callable=MockWorkerCompletion)

    response = flask_client.delete('/bee_tm/v1/task/')

    msg = response.get_json()['msg']
    print(msg)
    status = response.status_code
    assert status == 200
    assert msg.count('CANCELLED') == 3
