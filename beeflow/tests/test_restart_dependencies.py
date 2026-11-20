"""Restart identity regressions through WorkflowInterface and real storage."""

import sqlite3

import pytest

from beeflow.common.db import bdb
from beeflow.common.db.gdb_db import SQL_GDB
from beeflow.common.gdb.sqlite3_driver import SQLDriver
from beeflow.common.object_models import Hint, StepInput, StepOutput, Task, Workflow
from beeflow.common.wf_interface import WorkflowInterface


def exercise_restart_dependencies(wfi, edges, mode, name, reverse):
    """Exercise renamed, repeated restarts, including an already-restarted source.

    edges returns (dependent ID, predecessor ID, explicit flag) tuples from the
    real backend. Shared assertions run against SQLite and opt-in live Neo4j.
    """
    checkpoint = Hint(class_="beeflow:CheckpointRequirement", params={"num_tries": 4})
    source = Task(name="source", base_command=["true"], workflow_id=wfi.workflow_id,
                  hints=[checkpoint.model_copy(deep=True)])
    producer = Task(name=name, base_command=["true"], workflow_id=wfi.workflow_id,
                    hints=[checkpoint.model_copy(deep=True)],
                    depends_on=[source.name] if mode != "data" else [])
    explicit = Task(name="explicit", base_command=["true"], workflow_id=wfi.workflow_id,
                    depends_on=[producer.name])
    tasks = [source, producer, explicit]
    if mode != "explicit":
        source.outputs = [StepOutput(id="source/out", type="File", glob="seed.txt")]
        producer.inputs = [StepInput(id="seed", type="File", value="seed.txt",
                                      source="source/out")]
        producer.outputs = [StepOutput(id=f"{name}/out", type="File", glob="result.txt")]
        tasks.extend([
            Task(name="mixed", base_command=["true"], workflow_id=wfi.workflow_id,
                 inputs=[StepInput(id="input", type="File", value="stale.txt",
                                   source=f"{name}/out")], depends_on=[producer.name]),
            Task(name="data", base_command=["true"], workflow_id=wfi.workflow_id,
                 inputs=[StepInput(id="input", type="File", source=f"{name}/out")]),
        ])
    for task in reversed(tasks) if reverse else tasks:
        wfi.add_task(task)
    wfi.set_task_metadata(producer.id, {"preserved": "metadata"})

    # Restart an upstream task first. Later producer restarts must copy its
    # current predecessor ID, not resolve the authored name to an old attempt.
    wfi.set_task_state(source.id, "FAILED")
    new_source = wfi.restart_task(wfi.get_task_by_id(source.id), "/checkpoints/source")
    wfi.set_task_state(new_source.id, "COMPLETED")
    source_flag = int(mode != "data")
    assert (producer.id, new_source.id, source_flag) in edges()
    assert not any(dependency == source.id for _, dependency, _ in edges())

    dependents = tasks[2:]
    for attempt in range(2):
        wfi.set_task_state(producer.id, "FAILED")
        old = wfi.get_task_by_id(producer.id)
        replacement = wfi.restart_task(old, f"/checkpoints/attempt-{attempt}")
        assert replacement.id != old.id
        assert replacement.name != old.name
        assert wfi.get_task_state(old.id) == "RESTARTED"
        assert wfi.get_task_metadata(replacement.id) == {"preserved": "metadata"}
        assert not wfi.get_dependent_tasks(old.id)
        assert {task.id for task in wfi.get_dependent_tasks(replacement.id)} == {
            task.id for task in dependents
        }
        current_edges = edges()
        assert (replacement.id, new_source.id, source_flag) in current_edges
        assert (replacement.id, source.id, source_flag) not in current_edges
        for dependent in dependents:
            flag = int(dependent.name != "data")
            assert (dependent.id, replacement.id, flag) in current_edges
        # The old attempt is terminal, but the replacement is not. Filled data
        # on the mixed consumer must not bypass its explicit dependency gate.
        wfi._gdb_driver.initialize_ready_tasks(wfi.workflow_id)  # pylint: disable=W0212
        for dependent in dependents:
            assert wfi.get_task_state(dependent.id) == "WAITING"
        producer = replacement

    if mode != "explicit":
        wfi.set_task_output(producer.id, f"{name}/out", "result.txt")
    wfi.finalize_task(wfi.get_task_by_id(producer.id))
    for dependent in dependents:
        assert wfi.get_task_state(dependent.id) == "READY"
        if dependent.inputs:
            assert wfi.get_task_by_id(dependent.id).inputs[0].value == "result.txt"


@pytest.mark.parametrize("mode", ["explicit", "data", "mixed"])
@pytest.mark.parametrize("name", ["stage", "stage-7"])
@pytest.mark.parametrize("reverse", [False, True])
def test_sqlite_workflow_restart_dependencies(tmp_path, mode, name, reverse):
    """Exercise real WFI restarts without sharing the SQLDriver singleton."""
    graph = SQL_GDB(str(tmp_path / "graph.db"))
    driver = object.__new__(SQLDriver)
    driver.db = graph
    wfi = WorkflowInterface("restart-wf", gdb_driver=driver)
    wfi.initialize_workflow(Workflow(name="restart", id=wfi.workflow_id))

    def edges():
        return bdb.getall(graph.db_file,
                          "SELECT depending_task_id, depends_on_task_id, explicit FROM task_dep")

    exercise_restart_dependencies(wfi, edges, mode, name, reverse)


def test_sqlite_restart_rewiring_is_atomic(tmp_path):
    """A failure after copying edges rolls back rewiring and restart history."""
    graph = SQL_GDB(str(tmp_path / "graph.db"))
    graph.create_workflow(Workflow(name="restart", id="wf"))
    original = Task(name="setup", base_command=["true"], workflow_id="wf")
    dependent = Task(name="run", base_command=["true"], workflow_id="wf",
                     depends_on=[original.name])
    for task in [original, dependent]:
        graph.create_task(task)
        graph.add_dependencies(task)
    replacement = original.copy(update={"new_id": True, "name": "setup-1"})
    graph.create_task(replacement)
    with bdb.create_connection(graph.db_file) as connection:
        connection.execute(
            f"CREATE TRIGGER reject_delete BEFORE DELETE ON task_dep "
            f"WHEN OLD.depends_on_task_id = '{original.id}' "
            "BEGIN SELECT RAISE(ABORT, 'simulated rewire failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="simulated rewire failure"):
        graph.add_dependencies(replacement, old_task=original, restarted_task=True)
    assert bdb.getall(graph.db_file, "SELECT * FROM task_dep") == [
        (dependent.id, original.id, 1)
    ]
    assert bdb.getall(graph.db_file, "SELECT * FROM task_restart") == []
    assert bdb.getone(graph.db_file, "SELECT restart FROM workflow WHERE id='wf'") == (0,)
