"""Tests for the remote cli commands."""
import subprocess
import json
from typer.testing import CliRunner

from beeflow.client.remote_client import app


runner = CliRunner()  # Initialize the Typer test runner


def test_connection_success(mocker):
    """Test CLI connection command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/"], returncode=0,
        stdout='{"Endpoint info": "BEEflow core API: Documentation '
        '- https://lanl.github.io/BEE/"}',
        stderr=""
    )

    result = runner.invoke(app, ["connection", "ssh_target"])

    assert result.exit_code == 0
    expected_output = '{"Endpoint info": "BEEflow core API: Documentation ' \
                      '- https://lanl.github.io/BEE/"}'
    assert expected_output in result.output


def test_connection_failure_remote_not_started(mocker):
    """Test CLI connection command when the API call fails and remote API is not started."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["curl", "ssh_target:1234/"],
            stderr="Connection failed"
        ),
        subprocess.CompletedProcess(
            args='ssh {ssh_target} "ps aux | grep $USER | grep \'gunicorn\'"',
            returncode=0,
            stdout="",
            stderr=""
        )
    ]

    result = runner.invoke(app, ["connection", "ssh_target"])

    assert result.exit_code == 1
    assert "Connection to ssh_target:1234 failed." in result.output
    # It should warn that the remote API is not running.
    assert "Remote API has not been started on ssh_target. Use remote flag when starting beeflow." in result.output


def test_connection_failure_remote_started(mocker):
    """Test CLI connection command when the API call fails but remote API is started."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    # define subprocess output is remote api is running
    check_command_output = "Some process info ... beeflow.remote.remote:create_app ... more info"
    mock_run = mocker.patch("subprocess.run")
    mock_run.side_effect = [
        subprocess.CalledProcessError(
            returncode=1,
            cmd=["curl", "ssh_target:1234/"],
            stderr="Connection failed"
        ),
        subprocess.CompletedProcess(
            args='ssh {ssh_target} "ps aux | grep $USER | grep \'gunicorn\'"',
            returncode=0,
            stdout=check_command_output,
            stderr=""
        )
    ]

    result = runner.invoke(app, ["connection", "ssh_target"])

    assert result.exit_code == 1
    assert "Connection to ssh_target:1234 failed." in result.output
    # the warning about the remote API not being started should not appear.
    assert "Remote API has not been started on ssh_target." not in result.output


def test_droppoint_success(mocker):
    """Test CLI droppoint command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/droppoint"], returncode=0,
        stdout="droppoint_location", stderr=""
    )

    result = runner.invoke(app, ["droppoint", "ssh_target"])

    assert result.exit_code == 0

    mock_file.assert_called_once_with('droppoint.env', 'w', encoding='utf-8')
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/droppoint"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )


def test_droppoint_failure(mocker):
    """Test CLI droppoint command when the API call fails."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)

    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))
    result = runner.invoke(app, ["droppoint", "ssh_target"])

    assert result.exit_code != 0
    expected_output = 'Failed to retrieve droppoint from ssh_target:1234. ' \
                      'Check connection to beeflow.'
    assert expected_output in result.output


def test_copy_file_success(mocker):
    """Test copying a file to the droppoint successfully."""
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Patch builtins.open to simulate a valid droppoint.env file.
    mock_file = mocker.mock_open(read_data='{"droppoint": "/path/to/droppoint"}')
    mocker.patch("builtins.open", mock_file)

    # Patch subprocess.run for the rsync call.
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["rsync", "-a", "testfile.txt", "user@ssh_target:/path/to/droppoint"],
        returncode=0,
        stdout="",
        stderr=""
    )

    result = runner.invoke(app, ["copy", "user", "ssh_target", "testfile.txt"])
    assert result.exit_code == 0

    # Verify that droppoint.env was opened for reading.
    mock_file.assert_called_once_with("droppoint.env", "r", encoding="utf-8")

    # Verify the rsync command was called with the expected arguments.
    mock_run.assert_called_with(
        ["rsync", "-a", "testfile.txt", "user@ssh_target:/path/to/droppoint"],
        check=True
    )


def test_copy_droppoint_env_missing(mocker):
    """Test failure when the droppoint.env file is missing."""
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Simulate FileNotFoundError when trying to open droppoint.env.
    mocker.patch("builtins.open", side_effect=FileNotFoundError())

    result = runner.invoke(app, ["copy", "user", "ssh_target", "testfile.txt"])
    assert result.exit_code != 0


def test_copy_invalid_json(mocker):
    """Test failure when fetching droppoint fails."""
    mocker.patch("pathlib.Path.exists", return_value=True)

    # Simulate an invalid droppoint.env file by patching open.
    mock_file = mocker.mock_open(read_data="invalid json")
    mocker.patch("builtins.open", mock_file)

    result = runner.invoke(app, ["copy", "user", "ssh_target", "testfile.txt"])
    assert result.exit_code != 0

    mock_file.assert_called_once_with("droppoint.env", "r", encoding="utf-8")


def test_copy_rsync_fail(mocker):
    """Test failure when the rsync command fails."""
    mocker.patch("pathlib.Path.exists", return_value=True)

    mock_file = mocker.mock_open(read_data='{"droppoint": "/path/to/droppoint"}')
    mocker.patch("builtins.open", mock_file)

    # Patch subprocess.run so that the rsync call fails.
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "rsync"))

    result = runner.invoke(app, ["copy", "user", "ssh_target", "testfile.txt"])
    assert result.exit_code != 0

    mock_file.assert_called_once_with("droppoint.env", "r", encoding="utf-8")


def test_submit_success(mocker):
    """Test submit command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        returncode=0, stdout=json.dumps({"result": "Submitted new workflow test"}), stderr=""
    )

    result = runner.invoke(app,
            ["submit", "ssh_target", "workflow", "tarball", "main.cwl", "job.yaml"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )


def test_submit_failure(mocker):
    """Test submit command when the API call fails."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_run = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))

    result = runner.invoke(app,
            ["submit", "ssh_target", "workflow", "tarball", "main.cwl", "job.yaml"])

    assert result.exit_code != 0
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )


def test_core_status_success(mocker):
    """Test core-status command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
            ["curl", "ssh_target:1234/core/status/"], returncode=0,
            stdout='{"redis":"RUNNING","scheduler":"RUNNING","celery":"RUNNING",'
            '"slurmrestd":"RUNNING","wf_manager":"RUNNING","task_manager":"RUNNING",'
            '"remote_api":"RUNNING","neo4j-database":"RUNNING"}',
            stderr=""
    )

    result = runner.invoke(app, ["core-status", "ssh_target"])

    assert result.exit_code == 0
    expected_output = '{"redis":"RUNNING","scheduler":"RUNNING","celery":"RUNNING",' \
                      '"slurmrestd":"RUNNING","wf_manager":"RUNNING","task_manager":"RUNNING",' \
                      '"remote_api":"RUNNING","neo4j-database":"RUNNING"}'
    assert expected_output in result.output


def test_core_status_failure(mocker):
    """Test core-status command when the API call fails."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")
    mock_run = mocker.patch("subprocess.run")

    # Simulate a failed subprocess run
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["curl", "ssh_target:1234/core/status/"], stderr="Status check failed"
    )

    result = runner.invoke(app, ["core-status", "ssh_target"])

    assert result.exit_code == 1
    message = "Failed to check status on ssh_target:1234. Check connection to beeflow."
    assert message in result.output
