"""Tests for sql_gdb module."""

import sqlite3
from unittest.mock import call
import json

import pytest

from beeflow.common.db import bdb, gdb_db
from beeflow.common.object_models import StepInput, StepOutput, Task, Workflow


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

    incomplete_states = ["SUBMIT", "PENDING", "RUNNING", "COMPLETING"]
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


#
# Explicit (non-data) dependency and READY gate tests, against a real database
#

@pytest.fixture
def real_gdb(tmp_path):
    """Create an SQL_GDB instance backed by a real sqlite database."""
    return gdb_db.SQL_GDB(str(tmp_path / "gdb.db"))


def _init_workflow(gdb, wf_id="wf1"):
    """Create a workflow row for tasks to reference."""
    workflow = Workflow(name="test-wf", id=wf_id, workdir=".")
    gdb.create_workflow(workflow)
    return workflow


def _load_task(gdb, workflow_id, name, depends_on=None, inputs=None, outputs=None,
               state="WAITING"):
    """Create a task the way a driver's load_task does."""
    task = Task(
        name=name,
        base_command=["echo", name],
        workflow_id=workflow_id,
        state=state,
        inputs=inputs or [],
        outputs=outputs or [],
        depends_on=depends_on or [],
    )
    gdb.create_task(task)
    gdb.add_dependencies(task)
    return task


def test_explicit_dependency_loaded_first(real_gdb):
    """An explicit edge is written when the dependency is already loaded."""
    workflow = _init_workflow(real_gdb)
    setup = _load_task(real_gdb, workflow.id, "setup")
    run = _load_task(real_gdb, workflow.id, "run", depends_on=["setup"])

    dependents = real_gdb.get_dependent_tasks(setup.id)
    assert [task.id for task in dependents] == [run.id]


def test_explicit_dependency_loaded_second(real_gdb):
    """An explicit edge is written when the dependency loads afterwards."""
    workflow = _init_workflow(real_gdb)
    run = _load_task(real_gdb, workflow.id, "run", depends_on=["setup"])
    setup = _load_task(real_gdb, workflow.id, "setup")

    dependents = real_gdb.get_dependent_tasks(setup.id)
    assert [task.id for task in dependents] == [run.id]


def test_explicit_edge_upgrades_data_edge(real_gdb):
    """A pair that shares data and declares depends_on ends up explicit."""
    workflow = _init_workflow(real_gdb)
    producer = _load_task(
        real_gdb, workflow.id, "producer",
        outputs=[StepOutput(id="producer/out", type="String", glob=None)],
    )
    consumer = _load_task(
        real_gdb, workflow.id, "consumer",
        inputs=[StepInput(id="up", type="String", source="producer/out")],
        depends_on=["producer"],
    )

    rows = bdb.getall(
        real_gdb.db_file,
        "SELECT explicit FROM task_dep "
        "WHERE depending_task_id=? AND depends_on_task_id=?",
        [consumer.id, producer.id],
    )
    assert rows == [(1,)]


@pytest.mark.parametrize(
    "dependency_state, expected",
    [
        ("WAITING", "WAITING"),
        ("RUNNING", "WAITING"),
        ("COMPLETED", "READY"),
        ("RESTARTED", "READY"),
        ("FAILED", "READY"),
    ],
)
def test_ready_gate_explicit_dependency(real_gdb, dependency_state, expected):
    """A task with an explicit dependency only runs once it is final."""
    workflow = _init_workflow(real_gdb)
    _load_task(real_gdb, workflow.id, "setup", state=dependency_state)
    run = _load_task(real_gdb, workflow.id, "run", depends_on=["setup"])

    real_gdb.set_runnable_tasks_to_ready(workflow.id)

    assert real_gdb.get_task_state(run.id) == expected


def test_ready_gate_scoped_to_explicit(real_gdb):
    """Data-only dependencies keep input-based semantics (unchanged)."""
    workflow = _init_workflow(real_gdb)
    producer = _load_task(
        real_gdb, workflow.id, "producer",
        outputs=[StepOutput(id="producer/out", type="String", glob=None)],
    )
    # The consumer's input already has a value while the producer is WAITING
    consumer = _load_task(
        real_gdb, workflow.id, "consumer",
        inputs=[StepInput(id="up", type="String", value="filled",
                          source="producer/out")],
    )

    real_gdb.set_runnable_tasks_to_ready(workflow.id)

    assert real_gdb.get_task_state(consumer.id) == "READY"
    assert real_gdb.get_task_state(producer.id) == "READY"


def test_task_roundtrip_preserves_depends_on(real_gdb):
    """get_task reconstructs a task's depends_on list."""
    workflow = _init_workflow(real_gdb)
    _load_task(real_gdb, workflow.id, "setup")
    run = _load_task(real_gdb, workflow.id, "run", depends_on=["setup"])

    loaded = real_gdb.get_task(run.id)
    assert loaded.depends_on == ["setup"]


def test_task_roundtrip_preserves_multiple_base_commands(real_gdb):
    """Nested base_command lists survive sqlite JSON serialization."""
    workflow = _init_workflow(real_gdb)
    task = Task(
        name="multi",
        base_command=[["echo", "first"], ["echo", "second"]],
        workflow_id=workflow.id,
        inputs=[],
        outputs=[],
    )
    real_gdb.create_task(task)
    real_gdb.add_dependencies(task)

    loaded = real_gdb.get_task(task.id)
    assert loaded.base_command == [["echo", "first"], ["echo", "second"]]


def test_ensure_columns_migrates_old_schema(tmp_path):
    """Databases created before phase 2 gain the new columns."""
    db_file = str(tmp_path / "old.db")
    conn = sqlite3.connect(db_file)
    conn.execute(
        """CREATE TABLE task (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            name TEXT,
            state TEXT,
            workdir TEXT,
            base_command JSON,
            stdout TEXT,
            stderr TEXT,
            reqs JSON,
            hints JSON,
            metadata JSON
        )"""
    )
    conn.execute(
        """CREATE TABLE task_dep (
            depending_task_id TEXT NOT NULL,
            depends_on_task_id TEXT NOT NULL,
            PRIMARY KEY (depending_task_id, depends_on_task_id)
        )"""
    )
    conn.execute(
        "INSERT INTO task (id, workflow_id, name, state, base_command)"
        " VALUES ('t1', 'wf1', 'one', 'WAITING', '[]')"
    )
    conn.commit()
    conn.close()

    gdb_db.SQL_GDB(db_file)

    conn = sqlite3.connect(db_file)
    task_cols = {row[1] for row in conn.execute("PRAGMA table_info(task)")}
    dep_cols = {row[1] for row in conn.execute("PRAGMA table_info(task_dep)")}
    assert "depends_on" in task_cols
    assert "explicit" in dep_cols
    # Pre-existing rows read back with an empty depends_on list
    row = conn.execute("SELECT depends_on FROM task WHERE id='t1'").fetchone()
    assert json.loads(row[0]) == []
    conn.close()
