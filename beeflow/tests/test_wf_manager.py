"""Unit tests for the workflow manager."""

import tempfile
import os
import pathlib
import pytest
import jsonpickle

from test_parser import WORKFLOW_GOLD, TASKS_GOLD
from beeflow.wf_manager.wf_manager import create_app
from beeflow.wf_manager.resources import wf_utils
from beeflow.tests.mocks import MockWFI, MockGDBInterface
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.wf_interface import WorkflowInterface

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db

# We use this as the test workflow id
WF_ID = '42'


@pytest.fixture
def temp_db():
    """Pytest fixture for creating a temporary database."""
    fname = tempfile.mktemp(suffix='.db')
    db = connect_db(wfm_db, fname)
    yield db
    os.remove(fname)


@pytest.fixture
def app():
    """Create a new flask app object."""
    flask_app = create_app()
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
    wf_utils.create_workflow_dir(WF_ID)
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
def test_submit_workflow(client, mocker, teardown_workflow, temp_db):
    """Test submitting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.create_image',
                 return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.start_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.wait_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.kill_gdb', return_value=True)
    mocker.patch('beeflow.common.wf_data.generate_workflow_id', return_value='42')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=WorkflowInterface(MockGDBInterface()))
    mocker.patch('subprocess.run', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_list.db_path', temp_db.db_file)
    script_path = pathlib.Path(__file__).parent.resolve()
    tarball = script_path / 'clamr-wf.tgz'
    with open(tarball, 'rb') as tarball_contents:
        resp = client().post('/bee_wfm/v1/jobs/', data={
            'wf_name': 'clamr'.encode(),
            'wf_filename': tarball,
            'workdir': '.',
            'workflow': jsonpickle.encode(WORKFLOW_GOLD),
            'tasks': jsonpickle.encode(TASKS_GOLD, warn=True),
            'workflow_archive': tarball_contents
        })

    # Remove task added during the test
    assert resp.json['msg'] == 'Workflow uploaded'


def test_reexecute_workflow(client, mocker, teardown_workflow, temp_db):
    """Test reexecuting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.create_image',
                 return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.start_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.wait_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_list.dep_manager.kill_gdb', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_list.db_path', temp_db.db_file)
    mocker.patch('beeflow.common.wf_data.generate_workflow_id', return_value='42')
    mocker.patch('subprocess.run', return_value=True)

    script_path = pathlib.Path(__file__).parent.resolve()
    tarball = script_path / '42.tgz'
    with open(tarball, 'rb') as tarball_contents:
        resp = client().put('/bee_wfm/v1/jobs/', data={
                            'wf_filename': tarball,
                            'wf_name': 'clamr',
                            'workflow_archive': tarball_contents,
                            'workdir': '.'
                            })

        assert resp.json['msg'] == 'Workflow uploaded'


# WFActions Tests
def test_start_workflow(client, mocker, temp_db):
    """Test starting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)
    resp = client().post(f'/bee_wfm/v1/jobs/{WF_ID}')
    assert resp.status_code == 200


def test_workflow_status(client, mocker, setup_teardown_workflow, temp_db):
    """Test getting workflow status."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)
    wf_name = 'wf'
    wf_status = 'Pending'
    bolt_port = 3030
    gdb_pid = 12345

    temp_db.workflows.add_workflow(WF_ID, wf_name, wf_status, 'dir', bolt_port, gdb_pid)
    temp_db.workflows.add_task(123, WF_ID, 'task', "WAITING")
    temp_db.workflows.add_task(124, WF_ID, 'task', "RUNNING")

    resp = client().get(f'/bee_wfm/v1/jobs/{WF_ID}')
    assert 'RUNNING' in resp.json['tasks_status']


def test_cancel_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test cancelling a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)

    request = {'wf_id': WF_ID}
    resp = client().delete(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'Cancelled'
    assert resp.status_code == 202


def test_pause_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test pausing a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='RUNNING')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)

    wf_utils.update_wf_status(WF_ID, 'Running')
    request = {'option': 'pause'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'Workflow Paused'
    assert resp.status_code == 200


def test_resume_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test resuming a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='PAUSED')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)

    wf_utils.update_wf_status(WF_ID, 'Paused')
    request = {'option': 'resume'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['status'] == 'Workflow Resumed'
    assert resp.status_code == 200
# pylama:ignore=W0621,W0613
