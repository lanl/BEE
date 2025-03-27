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
    db.workflows.get_workflow_state.return_value = "Running"
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
            no_dag_dir=True
        )
        db.workflows.update_workflow_state.assert_called_once_with(
            "wf_id_test", expected_state
        )
        mock_update_wf_status.assert_called_once_with("wf_id_test", expected_state)
        mock_remove_wf_dir.assert_called_once_with("wf_id_test")
        mock_log.assert_called_once_with("Removing Workflow Directory")


@pytest.mark.parametrize("wf_state", ["Archived", "Archived/Failed"])
def test_archive_archived_wf(mocker, wf_state):
    """Don't archive workflow that is already archived."""
    db = mocker.MagicMock()
    db.workflows.get_workflow_state.return_value = wf_state
    mock_log_warning = mocker.patch("logging.Logger.warning")
    wf_update.archive_workflow(db, "id")
    mock_log_warning.assert_called_once_with(
        (
            "Attempted to archive workflow id which is already archived; "
            f"in state {wf_state}."
        )
    )


@pytest.mark.parametrize("job_state", ["FAILED", "SUBMIT_FAIL", 'BUILD_FAIL'])
def test_handle_state_change_failed_task(mocker, job_state):
    """Regression test task failure."""
    state_update = mocker.MagicMock()
    state_update.job_state = job_state
    task = mocker.MagicMock()
    task.name = "TestTask"
    wfi = mocker.MagicMock()
    wfi.workflow_completed.return_value = False
    wfi.cancelled_workflow_completed.return_value = False
    mock_archive_workflow = mocker.patch(
        "beeflow.wf_manager.resources.wf_update.archive_workflow"
    )
    db = mocker.MagicMock()
    mock_log_info = mocker.patch("logging.Logger.info")
    mock_set_dependent_tasks_dep_fail = mocker.patch(
        "beeflow.wf_manager.resources.wf_update.set_dependent_tasks_dep_fail"
    )
    workflow_update = wf_update.WFUpdate()
    workflow_update.handle_state_change(state_update, task, wfi, db)
    mock_log_info.assert_any_call("Task TestTask failed")
    mock_set_dependent_tasks_dep_fail.assert_called_once()
    mock_archive_workflow.assert_not_called()


@pytest.mark.parametrize(
    "completed, cancelled_completed, wf_state",
    [
        (True, False, ""),
        (False, True, "Cancelled"),
        (False, False, "Cancelled"),
        (False, True, ""),
    ],
)
def test_handle_state_change_completed_wf(
    mocker, completed, cancelled_completed, wf_state
):
    """Regression test when workflow is complete."""
    state_update = mocker.MagicMock()
    task = mocker.MagicMock()
    wfi = mocker.MagicMock()
    wfi.workflow_completed.return_value = completed
    wfi.cancelled_workflow_completed.return_value = cancelled_completed
    wfi.get_workflow_state.return_value = wf_state
    wfi.workflow_id = "TESTID"
    mock_archive_workflow = mocker.patch(
        "beeflow.wf_manager.resources.wf_update.archive_workflow"
    )
    db = mocker.MagicMock()
    mock_log_info = mocker.patch("logging.Logger.info")
    workflow_update = wf_update.WFUpdate()
    workflow_update.handle_state_change(state_update, task, wfi, db)
    print(mock_log_info.mock_calls)
    if completed:
        mock_log_info.assert_any_call("Workflow TESTID Completed")
        mock_log_info.assert_any_call("Workflow Archived")
        mock_archive_workflow.assert_called_once()
    elif cancelled_completed and wf_state == "Cancelled":
        mock_log_info.assert_any_call(
            "Scheduled tasks for cancelled workflow TESTID completed"
        )
        mock_log_info.assert_any_call("Workflow Archived")
        mock_archive_workflow.assert_called_once()
    else:
        mock_log_info.assert_not_called()
        mock_archive_workflow.assert_not_called()
