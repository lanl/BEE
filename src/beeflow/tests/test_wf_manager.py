import beeflow.wf_manager as wfm
import pytest
import requests
from mocks import MockWFI, mock_get
from mocks import mock_delete, mock_post, mock_put


@pytest.fixture
def flask_client():
    """Client runs flask queries."""
    app = wfm.flask_app
    app.config['TESTING'] = True
    client = app.test_client()
    return client


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_create_workflow(flask_client, mocker): # noqa
    """Create a workflow and get the ID back."""
    request = {'title': 'job',
               'filename': 'file.cwl'}

    response = flask_client.post('/bee_wfm/v1/jobs/', json=request)

    wf_id = response.get_json()['wf_id']
    status = response.status_code

    assert wf_id == '42'
    assert status == 201


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_submit_workflow(flask_client, mocker): # noqa
    """Submit a cwl file to the WFM. parse the cwl file."""
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)

    wf_id = 42

    files = {'workflow': open('src/beeflow/data/cwl/cf.cwl', 'rb')}
    response = flask_client.put('/bee_wfm/v1/jobs/submit/' + str(wf_id),
                                data=files)

    status = response.status_code
    assert status == 201


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_start_workflow(flask_client, mocker): # noqa
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)
    wf_id = 42
    request = {'wf_id': wf_id}

    mocker.patch.object(requests, 'post', side_effect=mock_post)
    mocker.patch.object(requests, 'put', side_effect=mock_put)
    response = flask_client.post('/bee_wfm/v1/jobs/' + str(wf_id), json=request)
    assert response.status_code == 200


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_query_workflow(flask_client, mocker): # noqa
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)
    wf_id = 42
    request = {'wf_id': wf_id}

    response = flask_client.get('/bee_wfm/v1/jobs/' + str(wf_id), json=request)
    tasks = response.json['msg'].split()
    assert tasks[0] == 'task1--RUNNING'
    assert response.status_code == 200


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_cancel_workflow(flask_client, mocker): # noqa
    mocker.patch.object(requests, 'delete', side_effect=mock_delete)
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)

    wf_id = 42
    request = {'wf_id': wf_id}

    response = flask_client.delete('/bee_wfm/v1/jobs/' + str(wf_id), json=request)
    assert response.json['status'] == 'cancelled'
    assert response.status_code == 202


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_pause_workflow(flask_client, mocker): # noqa
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)
    wf_id = 42
    request = {'wf_id': wf_id, 'option': 'pause'}

    response = flask_client.patch('/bee_wfm/v1/jobs/' + str(wf_id), json=request)
    assert response.json['status'] == 'Workflow Paused'
    assert response.status_code == 200


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_resume_workflow(flask_client, mocker): # noqa
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)
    wf_id = 42
    request = {'wf_id': wf_id, 'option': 'resume'}

    response = flask_client.patch('/bee_wfm/v1/jobs/' + str(wf_id), json=request)
    assert response.json['status'] == 'Workflow Resumed'
    assert response.status_code == 200


@pytest.mark.usefixtures('flask_client', 'mocker')
def test_update_task(flask_client, mocker): # noqa
    mocker.patch.object(requests, 'post', side_effect=mock_get)
    mocker.patch('beeflow.wf_manager.wfi', new_callable=MockWFI)

    task_id = 0
    job_state = 'COMPLETED'

    request = {'task_id': task_id, 'job_state': job_state}
    mocker.patch.object(requests, 'post', side_effect=mock_post)
    mocker.patch.object(requests, 'put', side_effect=mock_put)

    response = flask_client.put('/bee_wfm/v1/jobs/update/', json=request)

    assert response.json['status'] == f'Task {task_id} set to {job_state}'
    assert response.status_code == 200
