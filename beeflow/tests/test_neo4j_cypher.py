"""Tests for neo4j_cypher module."""

from unittest.mock import call
import pytest
from beeflow.common.gdb import neo4j_cypher
from beeflow.common.gdb.neo4j_driver import _reconstruct_task
from beeflow.common.object_models import Task


@pytest.mark.parametrize("reqs, expected", [(True, ["dummy"] * 3), (False, [])])
def test_get_workflow_requirements(mocker, reqs, expected):
    """Regression test get_workflow_requirements."""
    tx = mocker.MagicMock()
    tx.run.return_value = [{"r": e} for e in expected]
    mocker.patch(
        "beeflow.common.gdb.neo4j_cypher.get_workflow_by_id",
        return_value={"reqs": reqs},
    )
    result = neo4j_cypher.get_workflow_requirements(tx, "")
    assert result == expected


@pytest.mark.parametrize("hints, expected", [(True, ["dummy"] * 3), (False, [])])
def test_get_workflow_hints(mocker, hints, expected):
    """Regression test get_workflow_hints."""
    tx = mocker.MagicMock()
    tx.run.return_value = [{"h": e} for e in expected]
    mocker.patch(
        "beeflow.common.gdb.neo4j_cypher.get_workflow_by_id",
        return_value={"hints": hints},
    )
    result = neo4j_cypher.get_workflow_hints(tx, "")
    assert result == expected


@pytest.mark.parametrize("reqs, expected", [(True, ["dummy"] * 3), (False, [])])
def test_get_task_requirements(mocker, reqs, expected):
    """Regression test get_task_requirements."""
    tx = mocker.MagicMock()
    tx.run.return_value = [{"r": e} for e in expected]
    mocker.patch(
        "beeflow.common.gdb.neo4j_cypher.get_task_by_id",
        return_value={"reqs": reqs},
    )
    result = neo4j_cypher.get_task_requirements(tx, "")
    assert result == expected


@pytest.mark.parametrize("hints, expected", [(True, ["dummy"] * 3), (False, [])])
def test_get_task_hints(mocker, hints, expected):
    """Regression test get_task_hints."""
    tx = mocker.MagicMock()
    tx.run.return_value = [{"h": e} for e in expected]
    mocker.patch(
        "beeflow.common.gdb.neo4j_cypher.get_task_by_id",
        return_value={"hints": hints},
    )
    result = neo4j_cypher.get_task_hints(tx, "")
    assert result == expected


@pytest.mark.parametrize(
    "restart, single, expected",
    [
        (True, None, True),
        (False, None, True),
        (True, True, False),
        (False, True, False),
    ],
)
def test_final_tasks_completed(mocker, restart, single, expected):
    """Regression test final_tasks_completed."""
    tx = mocker.MagicMock()
    tx.run().single.return_value = single
    mocker.patch(
        "beeflow.common.gdb.neo4j_cypher.get_workflow_by_id",
        return_value={"restart": restart},
    )
    result = neo4j_cypher.final_tasks_completed(tx, "WFID")
    assert ("|RESTARTED_FROM" in tx.run.mock_calls[1].args[0]) == restart
    assert tx.run.mock_calls[2] == call().single()
    assert result == expected


@pytest.mark.parametrize("command", ["true", '["echo", "legacy"]', ["echo", "one"],
                                     [["echo", "one"], ["echo", "two"]]])
def test_command_storage_encoding(mocker, command):
    """Only nested commands need JSON; old string/list properties still decode."""
    transaction = mocker.MagicMock()
    task = Task(name="command", base_command=command, workflow_id="wf")
    neo4j_cypher.create_task(transaction, task)
    parameters = transaction.run.call_args.kwargs
    record = task.model_dump()
    record.update(base_command=parameters["base_command"],
                  base_command_json=parameters["base_command_json"])
    nested = isinstance(command, list) and isinstance(command[0], list)
    if nested:
        assert parameters["base_command"] is None
        assert isinstance(parameters["base_command_json"], str)
    else:
        assert parameters["base_command"] == command
        assert parameters["base_command_json"] is None
        # Existing nodes do not have the new property at all.
        record.pop("base_command_json")
    assert _reconstruct_task(record, [], [], [], [], {}).base_command == command
