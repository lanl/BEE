"""Unit tests for the workflow manager."""

import pathlib
import pytest
from beeflow.wf_manager.wf_manager import create_app
from beeflow.wf_manager.resources import wf_utils
from beeflow.wf_manager.common import dep_manager
from beeflow.tests.mocks import MockWFI, MockCwlParser
from beeflow.common.config_driver import BeeConfig as bc

# We use this as the test workflow id
WF_ID = '42'


@pytest.fixture
def app():
    """Create a new flask app object."""
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True
    })

    yield flask_app


@pytest.fixture()
def client(app):
    """Return the flask test client."""
    return app.test_client


@pytest.fixture()
def teardown_workflow():
    """Just tear down for tests that use the workflow directory."""
    yield
    wf_utils.remove_wf_dir(WF_ID)


@pytest.fixture()
def setup_teardown_workflow(teardown_workflow):
    """Set up and tear down for tests that use the workflow directory."""
    dep_manager.remove_current_run()
    wf_utils.create_wf_dir(WF_ID)
    wf_utils.create_wf_status(WF_ID)
    yield


def _url():
    """Return URL to the workflow manager end point."""
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    workflow_manager = 'bee_wfm/v1/jobs'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'


def _resource(tag=""):
    """Return the url for the workflow manager endpoint."""
    return _url() + str(tag)


# WFList Tests
def test_submit_workflow(client, mocker, teardown_workflow):
    """Test submitting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_list.CwlParser', new=MockCwlParser)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.create_image',
                 return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.remove_current_run',
                 return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.start_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.wait_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.kill_gdb', return_value=True)
    mocker.patch('subprocess.run', return_value=True)
    script_path = pathlib.Path(__file__).parent.resolve()
    tarball = script_path / 'clamr-wf.tgz'
    with open(tarball, 'rb') as tarball_contents:
        resp = client().post('/bee_wfm/v1/jobs/', data={
            'wf_name': 'clamr',
            'wf_filename': tarball,
            'main_cwl': 'clamr_wf.cwl',
            'yaml': 'clamr_job.yml',
            'workflow_archive': tarball_contents,
            'workdir': '.'
        })
        assert resp.json['msg'] == 'Workflow uploaded'


def test_reexecute_workflow(client, mocker, teardown_workflow):
    """Test reexecuting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_list.CwlParser', new=MockCwlParser)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.create_image',
                 return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.start_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.wait_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.kill_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.shutil.copytree', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('subprocess.run', return_value=True)

    wf_utils.create_current_run_dir()

    script_path = pathlib.Path(__file__).parent.resolve()
    tarball = script_path / '42.tgz'
    with open(tarball, 'rb') as tarball_contents:
        resp = client().put('/bee_wfm/v1/jobs/', data={
                            'wf_filename': tarball,
                            'wf_name': 'clamr',
                            'workflow_archive': tarball_contents
                            })

        wf_utils.remove_current_run_dir()
        assert resp.json['msg'] == 'Workflow uploaded'


# WFActions Tests
def test_start_workflow(client, mocker):
    """Test starting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)
    resp = client().post(f'/bee_wfm/v1/jobs/{WF_ID}')
    assert resp.status_code == 200


def test_workflow_status(client, mocker, setup_teardown_workflow):
    """Test getting workflow status."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    resp = client().get(f'/bee_wfm/v1/jobs/{WF_ID}')
    assert 'RUNNING' in resp.json['tasks_status']


def test_cancel_workflow(client, mocker, setup_teardown_workflow):
    """Test cancelling a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())

    request = {'wf_id': WF_ID}
    resp = client().delete(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'cancelled'
    assert resp.status_code == 202


def test_pause_workflow(client, mocker, setup_teardown_workflow):
    """Test pausing a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='RUNNING')

    wf_utils.update_wf_status(WF_ID, 'Running')
    request = {'option': 'pause'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'Workflow Paused'
    assert resp.status_code == 200


def test_resume_workflow(client, mocker, setup_teardown_workflow):
    """Test resuming a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='PAUSED')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)

    wf_utils.update_wf_status(WF_ID, 'Paused')
    request = {'option': 'resume'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'Workflow Resumed'
    assert resp.status_code == 200
# pylama:ignore=W0613,W0621