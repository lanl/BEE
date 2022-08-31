import pytest
from beeflow.wf_manager.wf_manager import create_app
import beeflow.wf_manager.resources.wf_utils as wf_utils
from beeflow.tests.mocks import MockWFI, MockCwlParser
from beeflow.common.config_driver import BeeConfig as bc

# We use this as the test workflow id
wf_id = '42'

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True
    })

    yield app

@pytest.fixture()
def client(app):
    return app.test_client


@pytest.fixture()
def teardown_workflow():
    yield
    wf_utils.remove_wf_dir(wf_id)


@pytest.fixture()
def setup_teardown_workflow(teardown_workflow):
    wf_utils.create_wf_dir(wf_id)
    wf_utils.create_wf_status(wf_id)
    yield


def _url():
    """Returns URL to the workflow manager end point"""
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    workflow_manager = 'bee_wfm/v1/jobs'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'


def _resource(tag=""):
    return _url() + str(tag)


# WFList Tests
def test_submit_workflow(client, mocker, teardown_workflow):
    """This function tests a user submitting a workflow to the POST in WFList"""
    mocker.patch('beeflow.wf_manager.resources.wf_list.CwlParser', new=MockCwlParser)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.create_image', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.start_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.wait_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.kill_gdb', return_value=True)
    mocker.patch('subprocess.run', return_value=True)
    tarball = 'clamr-wf.tgz'
    tarball_contents = open(tarball, 'rb')
    resp = client().post('/bee_wfm/v1/jobs/', data={
        'wf_name': 'clamr',
        'wf_filename': tarball,
        'main_cwl': 'clamr_wf.cwl',
        'yaml': 'clamr_job.yml',
        'workflow_archive': tarball_contents
    })
    assert resp.json['msg'] == 'Workflow uploaded'


def test_reexecute_workflow():
    pass


def test_copy_workflow():
    """Tests the copy workflow archive to PATCH in WFList"""
    pass


# WFActions Tests
def test_start_workflow(client, mocker):
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)
    resp = client().post(f'/bee_wfm/v1/jobs/{wf_id}')
    assert resp.status_code == 200


def test_workflow_status(client, mocker, setup_teardown_workflow):
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    resp = client().get(f'/bee_wfm/v1/jobs/{wf_id}')
    assert 'RUNNING' in resp.json['tasks_status']


def test_cancel_workflow(client, mocker, setup_teardown_workflow):
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())

    request = {'wf_id': wf_id}
    resp = client().delete(f'/bee_wfm/v1/jobs/{wf_id}', json=request)
    assert resp.json['status'] == 'cancelled'
    assert resp.status_code == 202


def test_pause_workflow(client, mocker, setup_teardown_workflow):
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='RUNNING')

    wf_utils.update_wf_status(wf_id, 'Running')
    request = {'option': 'pause'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{wf_id}', json=request)
    assert resp.json['status'] == 'Workflow Paused'
    assert resp.status_code == 200


def test_resume_workflow(client, mocker, setup_teardown_workflow):
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='PAUSED')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)

    wf_utils.update_wf_status(wf_id, 'Paused')
    request = {'option': 'resume'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{wf_id}', json=request)
    assert resp.json['status'] == 'Workflow Resumed'
    assert resp.status_code == 200
