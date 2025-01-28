"""Tests for wf_update module."""

import os
import pytest
from beeflow.wf_manager.resources import wf_update


@pytest.mark.parametrize(
    "test_function, expected_state",
    [
        (wf_update.archive_workflow, "Archived"),
        (wf_update.archive_fail_workflow, "Archived/Failed"),
    ],
)
def test_archive_workflow(tmpdir, mocker, test_function, expected_state):
    """Regression test archive_workflow."""
    workdir = str(tmpdir / "workdir")
    db = mocker.MagicMock()
    mocker.patch("os.path.expanduser", return_value=str(tmpdir))
    mocker.patch(
        "beeflow.wf_manager.resources.wf_utils.get_workflow_dir", return_value=workdir
    )
    mocker.patch(
        "beeflow.common.config_driver.BeeConfig.get",
        return_value=str(tmpdir / "bee_archive_dir"),
    )
    mock_export_dag = mocker.patch("beeflow.wf_manager.resources.wf_utils.export_dag")
    mock_update_wf_status = mocker.patch(
        "beeflow.wf_manager.resources.wf_utils.update_wf_status"
    )
    mock_remove_wf_dir = mocker.patch(
        "beeflow.wf_manager.resources.wf_utils.remove_wf_dir"
    )
    mock_log = mocker.patch("logging.Logger.info")
    with tmpdir.as_cwd():
        # set up dummy folders for archiving process
        os.makedirs(".config/beeflow")
        os.makedirs("workdir")
        os.makedirs("bee_archive_dir/workflows")
        with open(".config/beeflow/bee.conf", "w", encoding="utf-8"):
            pass
        test_function(db, "wf_id_test")
        assert os.path.exists("bee_archive_dir/wf_id_test.tgz")
        mock_export_dag.assert_called_once_with(
            "wf_id_test",
            workdir + "/dags",
            workdir + "/graphmls",
            no_dag_dir=True,
            copy_dag_in_archive=False,
        )
        db.workflows.update_workflow_state.assert_called_once_with(
            "wf_id_test", expected_state
        )
        mock_update_wf_status.assert_called_once_with("wf_id_test", expected_state)
        mock_remove_wf_dir.assert_called_once_with("wf_id_test")
        mock_log.assert_called_once_with("Removing Workflow Directory")
