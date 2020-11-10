import beeflow.task_manager.task_manager as tm
import beeflow
import flask_restful
from flask import Flask
import pytest
import jsonpickle
import requests
import os
from mocks import MockWFI, MockWorker, MockResponse, mock_put, mock_get, MockTask, mock_delete

@pytest.fixture
def flask_client():
    """This client lets us run flask queries"""
    app = tm.flask_app
    app.config['TESTING'] = True
    client = app.test_client()
    return client


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_submit_task(flask_client, mocker):
    """Create a workflow and get the ID back"""
    wfi = MockWFI() 
    task = list(wfi.get_dependent_tasks(wfi.get_task_by_id(0)))[0]
    task_json = jsonpickle.encode(task)

    response = flask_client.post('/bee_tm/v1/task/submit/', json={'task':task_json})

    mocker.patch('beeflow.task_manager.task_manager.worker',  
            new_callable=MockWorker)

    mocker.patch.object(requests, 'put', side_effect=mock_put)
    beeflow.task_manager.task_manager.process_queues()

    msg = response.get_json()['msg']
    status = response.status_code

    assert status == 200
    assert msg == 'Task Added!'



@pytest.mark.usefixtures('flask_client', 'mocker')
def test_remove_task(flask_client, mocker):
    wfi = MockWFI() 

    # Add a few tasks
    beeflow.task_manager.task_manager.job_queue.append({2 : {'name':'task1',
                                                        'job_id': 42,
                                                        'job_state': 'RUNNING'}})

    beeflow.task_manager.task_manager.job_queue.append({4 : {'name':'task2',
                                                        'job_id': 43,
                                                        'job_state': 'PENDING'}})

    beeflow.task_manager.task_manager.job_queue.append({6 : {'name':'task3',
                                                        'job_id': 44,
                                                        'job_state': 'PENDING'}})


    mocker.patch('beeflow.task_manager.task_manager.worker',  
            new_callable=MockWorker)

    response = flask_client.delete('/bee_tm/v1/task/')

    msg = response.get_json()['msg']
    print(msg)
    status = response.status_code
    assert status == 200
    assert msg.count('CANCELLED') == 3
