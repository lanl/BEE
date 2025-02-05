import pathlib
import subprocess
import pytest
from typer.testing import CliRunner

from beeflow.client.remote_client import app


runner = CliRunner()  # Initialize the Typer test runner


def test_connection_success(mocker):
    """Test CLI connection command when the API call succeeds."""
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/"], returncode=0,
        stdout='{"Endpoint info": "BEEflow core API: Documentation '
        '- https://lanl.github.io/BEE/"}',
        stderr=""
    )

    result = runner.invoke(app, ["connection", "ssh_target"])

    assert result.exit_code == 0
    assert '{"Endpoint info": "BEEflow core API: Documentation '
    '- https://lanl.github.io/BEE/"}' in result.output


def test_droppoint_success(mocker):
    """Test CLI droppoint command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_file = mocker.mock_open()
    mocker.patch("builtins.open", mock_file)

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/droppoint"], returncode=0, stdout="droppoint_location", stderr=""
    )

    result = runner.invoke(app, ["droppoint", "ssh_target"])

    assert result.exit_code == 0

    mock_file.assert_called_once_with('droppoint.env', 'w', encoding='utf-8')
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/droppoint"], stdout=mock_file(), check=True
    )


def test_copy_file_success(mocker):
    """Test copying a file to the droppoint successfully."""
    mock_droppoint = mocker.patch("subprocess.run")

    # Mock the first subprocess.run call to return a valid droppoint
    mock_droppoint.side_effect = [
        subprocess.CompletedProcess(args=["jq", "-r", ".droppoint", "droppoint.env"], returncode=0, stdout="remote:/path/to/droppoint\n"),
        subprocess.CompletedProcess(args=["scp", "testfile.txt", "remote:/path/to/droppoint"], returncode=0)
    ]

    mocker.patch("pathlib.Path.is_dir", return_value=False)

    result = runner.invoke(app, ["copy", "testfile.txt"])

    assert result.exit_code == 0

    # Ensure subprocess.run was called to fetch droppoint
    mock_droppoint.assert_any_call(
        ["jq", "-r", ".droppoint", "droppoint.env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    # Ensure subprocess.run was called with correct scp command
    mock_droppoint.assert_any_call(
        ["scp", "testfile.txt", "remote:/path/to/droppoint"],
        check=True
    )


def test_copy_directory_success(mocker):
    """Test copying a directory to the droppoint successfully."""
    mock_droppoint = mocker.patch("subprocess.run")

    # Mock subprocess responses
    mock_droppoint.side_effect = [
        subprocess.CompletedProcess(args=["jq", "-r", ".droppoint", "droppoint.env"], returncode=0, stdout="remote:/path/to/droppoint\n"),
        subprocess.CompletedProcess(args=["scp", "-r", "testdir", "remote:/path/to/droppoint"], returncode=0)
    ]

    mocker.patch("pathlib.Path.is_dir", return_value=True)

    result = runner.invoke(app, ["copy", "testdir"])

    assert result.exit_code == 0

    # Ensure subprocess.run was called to fetch droppoint
    mock_droppoint.assert_any_call(
        ["jq", "-r", ".droppoint", "droppoint.env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    # Ensure subprocess.run was called with correct scp command for a directory
    mock_droppoint.assert_any_call(
        ["scp", "-r", "testdir", "remote:/path/to/droppoint"],
        check=True
    )


def test_copy_droppoint_fetch_fail(mocker):
    """Test failure when fetching droppoint fails."""
    mock_droppoint = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "jq"))

    result = runner.invoke(app, ["copy", "testfile.txt"])

    assert result.exit_code != 0  # Ensure it fails


def test_copy_scp_fail(mocker):
    """Test failure when scp command fails."""
    mock_droppoint = mocker.patch("subprocess.run")

    # First subprocess call succeeds (droppoint lookup)
    mock_droppoint.side_effect = [
        subprocess.CompletedProcess(args=["jq", "-r", ".droppoint", "droppoint.env"], returncode=0, stdout="remote:/path/to/droppoint\n"),
        subprocess.CalledProcessError(1, "scp")  # Simulate scp failure
    ]

    result = runner.invoke(app, ["copy", "testfile.txt"])


def test_submit_success(mocker):
    """Test submit command when the API call succeeds."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        returncode=0
    )

    result = runner.invoke(app, ["submit", "ssh_target", "workflow", "tarball", "main.cwl", "job.yaml"])

    assert result.exit_code == 0  # Ensure the command succeeds
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        check=True
    )


def test_submit_failure(mocker):
    """Test submit command when the API call fails."""
    mocker.patch("beeflow.client.remote_client.remote_port_val", return_value="1234")

    mock_run = mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "curl"))

    result = runner.invoke(app, ["submit", "ssh_target", "workflow", "tarball", "main.cwl", "job.yaml"])

    assert result.exit_code != 0  # Ensure the command fails
    mock_run.assert_called_once_with(
        ["curl", "ssh_target:1234/submit_long/workflow/tarball/main.cwl/job.yaml"],
        check=True
    )
