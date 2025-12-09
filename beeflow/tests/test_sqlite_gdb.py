"""Tests for sql_gdb module."""

from unittest.mock import call
import json

import pytest

from beeflow.common.db import gdb_db


@pytest.fixture
def sql_gdb_instance(mocker, tmp_path):
    """Create SQL_GDB instance with bdb.create_table/runscript patched."""
    mocker.patch("beeflow.common.db.gdb_db.bdb.create_table")
    mocker.patch("beeflow.common.db.gdb_db.bdb.runscript")
    db_file = tmp_path / "test.db"
    return gdb_db.SQL_GDB(str(db_file))


@pytest.mark.parametrize("count, expected", [(0, True), (3, False)])
def test_final_tasks_completed(mocker, sql_gdb_instance, count, expected):
    """Regression test final_tasks_completed."""
    getone = mocker.patch(
        "beeflow.common.db.gdb_db.bdb.getone",
        return_value=(count,),
    )

    wf_id = "WFID"
    result = sql_gdb_instance.final_tasks_completed(wf_id)

    placeholders = ",".join("?" for _ in gdb_db.final_task_states)
    expected_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state NOT IN ({placeholders});
        """

    getone.assert_called_once()
    assert getone.mock_calls[0] == call(
        sql_gdb_instance.db_file,
        expected_query,
        [wf_id, *gdb_db.final_task_states],
    )
    assert result == expected


@pytest.mark.parametrize(
    "completed, failed_count, expected",
    [
        (True, 0, True),   # all completed, none failed
        (True, 2, False),  # completed but some failed
        (False, 0, False), # not completed yet
    ],
)
def test_final_tasks_succeeded(mocker, sql_gdb_instance, completed, failed_count, expected):
    """Regression test final_tasks_succeeded."""
    mocker.patch.object(
        gdb_db.SQL_GDB,
        "final_tasks_completed",
        return_value=completed,
    )
    getone = mocker.patch(
        "beeflow.common.db.gdb_db.bdb.getone",
        return_value=(failed_count,),
    )

    wf_id = "WFID"
    result = sql_gdb_instance.final_tasks_succeeded(wf_id)

    placeholders = ",".join("?" for _ in gdb_db.failed_task_states)
    expected_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state IN ({placeholders});
        """

    getone.assert_called_once()
    assert getone.mock_calls[0] == call(
        sql_gdb_instance.db_file,
        expected_query,
        [wf_id, *gdb_db.failed_task_states],
    )
    assert result == expected


@pytest.mark.parametrize("count, expected", [(0, True), (5, False)])
def test_final_tasks_failed(mocker, sql_gdb_instance, count, expected):
    """Regression test final_tasks_failed."""
    getone = mocker.patch(
        "beeflow.common.db.gdb_db.bdb.getone",
        return_value=(count,),
    )

    wf_id = "WFID"
    result = sql_gdb_instance.final_tasks_failed(wf_id)

    placeholders = ",".join("?" for _ in gdb_db.failed_task_states) + ",?"
    expected_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state NOT IN ({placeholders});
        """

    getone.assert_called_once()
    assert getone.mock_calls[0] == call(
        sql_gdb_instance.db_file,
        expected_query,
        [wf_id, *gdb_db.failed_task_states, "RESTARTED"],
    )
    assert result == expected


@pytest.mark.parametrize("count, expected", [(0, True), (1, False)])
def test_cancelled_final_tasks_completed(mocker, sql_gdb_instance, count, expected):
    """Regression test cancelled_final_tasks_completed."""
    getone = mocker.patch(
        "beeflow.common.db.gdb_db.bdb.getone",
        return_value=(count,),
    )

    wf_id = "WFID"
    result = sql_gdb_instance.cancelled_final_tasks_completed(wf_id)

    incomplete_states = ["PENDING", "RUNNING", "COMPLETING"]
    placeholders = ",".join("?" for _ in incomplete_states)
    expected_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state IN ({placeholders});
        """

    getone.assert_called_once()
    assert getone.mock_calls[0] == call(
        sql_gdb_instance.db_file,
        expected_query,
        [wf_id, *incomplete_states],
    )
    assert result == expected


@pytest.mark.parametrize(
    "db_value, expected",
    [
        (None, {}),
        ((None,), {}),
        ((json.dumps({"a": 1}),), {"a": 1}),
    ],
)
def test_get_task_metadata(mocker, sql_gdb_instance, db_value, expected):
    """Regression test get_task_metadata."""
    getone = mocker.patch(
        "beeflow.common.db.gdb_db.bdb.getone",
        return_value=db_value,
    )

    task_id = "TASK1"
    result = sql_gdb_instance.get_task_metadata(task_id)

    getone.assert_called_once_with(
        sql_gdb_instance.db_file,
        "SELECT metadata FROM task WHERE id=?",
        [task_id],
    )
    assert result == expected


def test_set_task_metadata_merges_existing(mocker, sql_gdb_instance):
    """Regression test set_task_metadata merges prior and new metadata."""
    task_id = "TASK1"
    mocker.patch.object(
        gdb_db.SQL_GDB,
        "get_task_metadata",
        return_value={"a": 1, "b": 2},
    )
    run = mocker.patch("beeflow.common.db.gdb_db.bdb.run")

    sql_gdb_instance.set_task_metadata(task_id, {"b": 3, "c": 4})

    # Extract the JSON written to the DB and verify merge result.
    assert run.call_count == 1
    _, args, _ = run.mock_calls[0]
    assert args[0] == sql_gdb_instance.db_file
    assert args[1] == "UPDATE task SET metadata=? WHERE id=?"
    metadata_json, called_task_id = args[2]
    assert called_task_id == task_id
    merged = json.loads(metadata_json)
    assert merged == {"a": 1, "b": 3, "c": 4}


def test_set_task_state(mocker, sql_gdb_instance):
    """Regression test set_task_state issues correct UPDATE."""
    run = mocker.patch("beeflow.common.db.gdb_db.bdb.run")

    sql_gdb_instance.set_task_state("TASK1", "RUNNING")

    run.assert_called_once_with(
        sql_gdb_instance.db_file,
        """
            UPDATE task
            SET state = :state
            WHERE id = :task_id;""",
        {"task_id": "TASK1", "state": "RUNNING"},
    )


def test_set_workflow_state(mocker, sql_gdb_instance):
    """Regression test set_workflow_state issues correct UPDATE."""
    run = mocker.patch("beeflow.common.db.gdb_db.bdb.run")

    sql_gdb_instance.set_workflow_state("WFID", "COMPLETED")

    run.assert_called_once_with(
        sql_gdb_instance.db_file,
        """
            UPDATE workflow
            SET state = :state
            WHERE id = :wf_id;""",
        {"wf_id": "WFID", "state": "COMPLETED"},
    )
