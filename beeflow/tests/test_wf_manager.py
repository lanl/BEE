"""Unit tests for the workflow manager."""

# pylint:disable=W0621,W0613

import tempfile
import os
import pathlib
import pytest
import base64

from beeflow.common.object_models import Task

from beeflow.wf_manager.models import SubmitWorkflowRequest
from test_parser import WORKFLOW_GOLD, TASKS_GOLD
from beeflow.wf_manager.wf_manager import create_app
from beeflow.wf_manager.resources import wf_utils
from beeflow.tests.mocks import MockWFI, MockGDBDriver
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
    yield


def _url():
    """Return URL to the workflow manager end point."""
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    workflow_manager = 'bee_wfm/v1/jobs'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'


def _resource(tag=""):
    """Return the url for the workflow manager endpoint."""
    return _url() + str(tag)


class MockTask:
    """Mock task class for mocking celery."""

    @staticmethod
    def delay(*pargs, **kwargs):
        """Mock a delay call to the celery backend."""
        return None


# WFList Tests
def test_submit_workflow(client, mocker, teardown_workflow, temp_db):
    """Test submitting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.start_workflow', new=MockTask)

    mocker.patch('beeflow.common.object_models.generate_workflow_id', return_value='42')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=WorkflowInterface(WORKFLOW_GOLD.id, MockGDBDriver()))

    mocker.patch('subprocess.run', return_value=True)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_list.db_path', temp_db.db_file)
    script_path = pathlib.Path(__file__).parent.resolve()
    tarball = script_path / 'clamr-wf.tgz'
    with open(tarball, 'rb') as tarball_contents:
        payload = SubmitWorkflowRequest(
            wf_name='clamr',
            wf_filename=str(tarball),
            wf_workdir='.',
            no_start=False,
            workflow=WORKFLOW_GOLD,
            tasks=TASKS_GOLD,
            encoded_tarball=base64.b64encode(tarball_contents.read()).decode('utf-8'),
        )
        resp = client().post(
            '/bee_wfm/v1/jobs/', json=payload.model_dump())

    # Remove task added during the test
    print(resp)
    assert resp.json['msg'] == 'Workflow uploaded'


class MockDBWorkflowHandle:
    """Mock DB workflow handle."""

    def update_workflow_state(self, *pargs, **kwargs):
        """Mock update a workflow."""


class MockDB:
    """Mock DB for workflow manager."""

    @property
    def workflows(self):
        """Return a workflow handle."""
        return MockDBWorkflowHandle()


def mock_connect_db(*pargs, **kwargs):
    """Mock a DB connection."""
    return MockDB()


# WFActions Tests
def test_start_workflow(client, mocker):
    """Test starting a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state', return_value='No Start')
    resp = client().post(f'/bee_wfm/v1/jobs/{WF_ID}')
    assert resp.status_code == 200
    assert resp.json['msg'] == 'Workflow started successfully'


def test_workflow_status(client, mocker, setup_teardown_workflow):
    """Test getting workflow status."""

    mockGDB = MockGDBDriver()
    mockGDB.workflow_state = 'Running'
    mockGDB.tasks = {'123':Task(
        id='123',
        workflow_id=WF_ID,
        name='task',
        base_command='',
        state='RUNNING'
    ), '124': Task(
        id='124',
        workflow_id=WF_ID,
        name='task',
        base_command='',
        state='WAITING'
    )}
    mockGDB.task_states = {
        '123': 'RUNNING',
        '124': 'WAITING',
    }
    mockGDB.task_metadata = {
        '123': {'key': 'value'},
        '124': {'key': 'value'},
    }


    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=WorkflowInterface(WF_ID, gdb_driver=mockGDB))
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_wf_status',
                 return_value='Running')

    resp = client().get(f'/bee_wfm/v1/jobs/{WF_ID}')
    wf_status = resp.json['wf_status']
    assert wf_status == 'Running'

    tasks_status = resp.json['tasks_status']
    assert len(tasks_status) == 2
    sorted_status = sorted(tasks_status, key=lambda x: x[0])
    assert sorted_status[0][0] == '123'
    assert sorted_status[0][1] == 'task'
    assert sorted_status[0][2] == 'RUNNING'
    assert sorted_status[1][0] == '124'
    assert sorted_status[1][1] == 'task'
    assert sorted_status[1][2] == 'WAITING'


def test_cancel_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test cancelling a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.db_path', temp_db.db_file)
    mocker.patch('beeflow.wf_manager.resources.wf_actions.archive_workflow', return_value=None)

    wf_name = 'wf'
    workdir = 'dir'

    temp_db.workflows.init_workflow(WF_ID, wf_name, workdir)
    temp_db.workflows.add_task(123, WF_ID, 'task', "WAITING")
    temp_db.workflows.add_task(124, WF_ID, 'task', "RUNNING")

    request = {'wf_id': WF_ID, 'option': 'cancel'}
    resp = client().delete(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['msg'] == 'Workflow cancelled successfully'
    assert resp.status_code == 202


def test_remove_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test removing a workflow."""
    mockGDB = MockGDBDriver()
    mockGDB.workflow_state = 'Cancelled'
    mockGDB.tasks = {'123':Task(
        id='123',
        workflow_id=WF_ID,
        name='task',
        base_command='',
    ), '124': Task(
        id='124',
        workflow_id=WF_ID,
        name='task',
        base_command='',
    )}
    mockGDB.task_states = {
        '123': 'RUNNING',
        '124': 'WAITING',
    }


    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=WorkflowInterface(WF_ID, gdb_driver=mockGDB))

    request = {'wf_id': WF_ID, 'option': 'remove'}
    resp = client().delete(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['msg'] == 'Workflow removed successfully'
    assert resp.status_code == 202


def test_pause_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test pausing a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_wf_status', 
                 return_value='Running')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', 
                 return_value=None)
    request = {'option': 'pause'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['msg'] == 'Workflow Paused'
    assert resp.status_code == 200


def test_resume_workflow(client, mocker, setup_teardown_workflow, temp_db):
    """Test resuming a workflow."""
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface',
                 return_value=MockWFI())
    mocker.patch('beeflow.tests.mocks.MockWFI.get_workflow_state',
                 return_value='Paused')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_tm', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.submit_tasks_scheduler', return_value=None)
    mocker.patch('beeflow.wf_manager.resources.wf_utils.update_wf_status', return_value=None)

    wf_utils.update_wf_status(WF_ID, 'Paused')
    request = {'option': 'resume'}
    resp = client().patch(f'/bee_wfm/v1/jobs/{WF_ID}', json=request)
    assert resp.json['msg'] == 'Workflow Resumed'
    assert resp.status_code == 200
