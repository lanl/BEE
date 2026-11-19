"""Tests for wf_utils module."""
# Disable W0621: Redefinition of names is required for pytest fixtures
# pylint:disable=W0621

import pytest
from beeflow.wf_manager.resources import wf_utils

from beeflow.tests.mocks import MockWFI


@pytest.mark.parametrize(
    "which_return, no_dag_flag, expected_dot_avail",
    [
        ("/usr/bin/dot", True, True),
        ("/usr/bin/dot", False, True),
        (None, True, False),
        (None, False, False),
    ],
)
def test_export_dag(mocker, which_return, no_dag_flag, expected_dot_avail):
    """Regression test export_dag based on graphviz availability."""
    wf_id = "abc123"
    output_dir = "/path/to/out"
    graphmls_dir = "/path/to/gmls"
    workflow_dir = "/path/to/wfdir"
    
    mock_wfi = mocker.MagicMock()
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface', return_value=mock_wfi)
    mocker.patch('beeflow.common.wf_interface.WorkflowInterface.export_graphml')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.shutil.which',
                 return_value=which_return)
    mock_update = mocker.patch('beeflow.wf_manager.resources.wf_utils.update_graphml')
    mock_viz = mocker.patch('beeflow.wf_manager.resources.wf_utils.generate_viz')

    result =  wf_utils.export_dag(
        wf_id,
        output_dir,
        graphmls_dir,
        no_dag_flag,
        workflow_dir
    )

    # always export the GraphML first
    mock_wfi.export_graphml.assert_called_once_with()

    # return value is bool(shutil.which)
    assert result is expected_dot_avail

    if expected_dot_avail:
        mock_update.assert_called_once_with(wf_id, graphmls_dir)
        mock_viz.assert_called_once_with(
            wf_id, output_dir, graphmls_dir, no_dag_flag, workflow_dir
        )
    else:
        mock_update.assert_called_once_with(
            wf_id, graphmls_dir, output_dir, no_dag_flag
        )
        mock_viz.assert_not_called()







@pytest.fixture
def bee_paths(mocker, tmp_path):
    """Mock bee paths into tmp_path."""
    bee_workdir = tmp_path / "bee_workdir"
    archive_dir = bee_workdir / "archives"
    (bee_workdir / "workflows").mkdir(parents=True)

    values = {
        ("DEFAULT", "bee_workdir"): str(bee_workdir),
        ("DEFAULT", "bee_archive_dir"): str(archive_dir),
        ("DEFAULT", "delete_completed_workflow_dirs"): True,
        ("graphdb", "type"): "sqlite3",
    }
    mocker.patch("beeflow.common.config_driver.BeeConfig.get",
                 side_effect=lambda section, option, *_a, **_kw: values[(section, option)])
    return bee_workdir, archive_dir


def test_retry_restores_wf_dir_and_final_archive_complete(mocker, tmp_path, bee_paths):
    """Final archive after retry keeps submit-time files."""
    # pylint: disable=C0415
    import tarfile
    from beeflow.wf_manager.resources import wf_update

    wf_id = "wf_retry_test"
    bee_workdir, archive_dir = bee_paths
    home = tmp_path / "home"
    (home / ".config" / "beeflow").mkdir(parents=True)
    (home / ".config" / "beeflow" / "bee.conf").write_text("")
    mocker.patch("os.path.expanduser", return_value=str(home))

    state = {"value": "Running"}
    mocker.patch("beeflow.wf_manager.resources.wf_utils.get_wf_status",
                 side_effect=lambda _wf_id: state["value"])
    mocker.patch("beeflow.wf_manager.resources.wf_utils.update_wf_status",
                 side_effect=lambda _wf_id, msg: state.update(value=msg))
    mock_wfi = mocker.MagicMock()
    mock_wfi.get_workflow_state.side_effect = lambda: state["value"]
    mocker.patch("beeflow.wf_manager.resources.wf_utils.get_workflow_interface",
                 return_value=mock_wfi)
    mock_start = mocker.patch("beeflow.wf_manager.resources.wf_utils.start_workflow")

    # Submit-time files
    wf_dir = bee_workdir / "workflows" / wf_id
    (wf_dir / "cwl_files").mkdir(parents=True)
    (wf_dir / "cwl_files" / "workflow.cwl").write_text("cwl")
    (wf_dir / "submit_command_args.yaml").write_text("wf_name: test\n")
    (wf_dir / "bee_wf_name").write_text("test")
    (wf_dir / "workflow.tgz").write_bytes(b"tarball")

    # Fail -> archive + remove dir
    wf_update.archive_fail_workflow(wf_id)
    assert not wf_dir.exists()

    # Retry restores dir
    wf_utils.retry_failed_workflow(wf_id)
    mock_start.delay.assert_called_once_with(wf_id)
    assert (wf_dir / "submit_command_args.yaml").exists()

    # Re-archive after retried task
    (wf_dir / "task-abcd").mkdir(exist_ok=True)
    (wf_dir / "task-abcd" / "task-abcd.out").write_text("out")
    wf_update.archive_workflow(wf_id, final_state="Completed")

    with tarfile.open(archive_dir / f"{wf_id}.tgz") as archive:
        names = set(archive.getnames())
    for expected in ("submit_command_args.yaml", "bee_wf_name", "workflow.tgz",
                     "cwl_files/workflow.cwl", "task-abcd/task-abcd.out"):
        assert f"{wf_id}/{expected}" in names


def test_restore_wf_dir_noop_when_dir_exists(mocker, bee_paths):
    """No restore if dir exists."""
    bee_workdir, _ = bee_paths
    (bee_workdir / "workflows" / "wf").mkdir()
    mock_run = mocker.patch("beeflow.wf_manager.resources.wf_utils.subprocess.run")
    wf_utils.restore_wf_dir_from_archive("wf")
    mock_run.assert_not_called()


@pytest.mark.usefixtures("bee_paths")
def test_restore_wf_dir_no_archive(mocker):
    """Warn if no archive."""
    mock_run = mocker.patch("beeflow.wf_manager.resources.wf_utils.subprocess.run")
    mock_warn = mocker.patch("logging.Logger.warning")
    wf_utils.restore_wf_dir_from_archive("wf")
    mock_run.assert_not_called()
    mock_warn.assert_called_once()
