"""Beeflow REST API tests."""
import pathlib
from fastapi.testclient import TestClient

from beeflow.remote.remote import app
from beeflow.common import paths

client = TestClient(app)


def test_read_root():
    """Test the root endpoint of the FastAPI app."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "Endpoint info": "BEEflow core API: Documentation - https://lanl.github.io/BEE/"
    }


def test_get_drop_point():
    """Test the `/droppoint` endpoint."""
    response = client.get("/droppoint")
    assert response.status_code == 200

    expected_droppoint = str(paths.droppoint_root())
    response_json = response.json()

    assert "droppoint" in response_json  # Ensure the key exists
    assert response_json["droppoint"] == expected_droppoint  # Validate the path matches


def test_get_owner(monkeypatch):
    """Test the /owner endpoint."""
    mock_user = "test_user"
    monkeypatch.setenv("USER", mock_user)

    response = client.get("/owner")
    assert response.status_code == 200
    assert response.json() == mock_user


def test_submit_new_wf_long(mocker):
    """Test the /submit_long endpoint."""
    mocker.patch("beeflow.common.paths.droppoint_root", return_value="/mock/droppoint")
    mocker.patch("os.path.exists", return_value=True)

    mock_submit = mocker.patch("beeflow.client.bee_client.submit")
    mock_submit.return_value = None  # Simulate successful submission

    # Define test parameters
    wf_name = "test_workflow"
    tarball_name = "test_workflow.tgz"
    main_cwl_file = "main.cwl"
    job_file = "job.json"

    # Send request
    response = client.get(f"/submit_long/{wf_name}/{tarball_name}/{main_cwl_file}/{job_file}")

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"result": "Submitted new workflow " + wf_name}
    mock_submit.assert_called_once_with(
        wf_name,
        pathlib.Path("/mock/droppoint/test_workflow.tgz"),
        main_cwl_file,
        job_file,
        pathlib.Path("/mock/droppoint/test_workflow-workdir"),
        no_start=False
    )


def test_get_core_status(mocker):
    """Test the /core/status/ endpoint."""
    mocker.patch("beeflow.common.paths.beeflow_socket", return_value="/mock/socket")

    # Mocked response from the daemon
    mock_response = {
        "components": {
            "scheduler": "running",
            "wf_manager": "running",
            "task_manager": "running"
        }
    }

    mock_send = mocker.patch("beeflow.common.cli_connection.send")
    mock_send.return_value = mock_response  # Return fake status

    response = client.get("/core/status/")

    assert response.status_code == 200
    assert response.json() == {
        "scheduler": "running",
        "wf_manager": "running",
        "task_manager": "running"
    }
    mock_send.assert_called_once_with("/mock/socket", {"type": "status"})


def test_get_core_status_failure(mocker):
    """Test failure case when the beeflow daemon is not reachable."""
    mocker.patch("beeflow.common.paths.beeflow_socket", return_value="/mock/socket")

    mock_send = mocker.patch("beeflow.common.cli_connection.send")
    mock_send.return_value = None

    response = client.get("/core/status/")

    assert response.status_code == 200
    assert response.json() == {
        "error": "Cannot connect to the beeflow daemon, is it running?"
    }
    mock_send.assert_called_once_with("/mock/socket", {"type": "status"})
