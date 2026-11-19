"""Opt-in live Neo4j phase-2 checks; all test writes are rolled back.

Set BEE_TEST_NEO4J_URI to a disposable, authentication-disabled Neo4j 5
instance (for example bolt://127.0.0.1:17687) to run these tests.
"""

import os
from uuid import uuid4

from neo4j import GraphDatabase
import pytest

from beeflow.common.gdb import neo4j_cypher as cypher
from beeflow.common.gdb.neo4j_driver import _reconstruct_task
from beeflow.common.object_models import StepInput, Task


@pytest.fixture
def live_graph():
    """Use a unique workflow in a transaction that is never committed."""
    uri = os.environ.get("BEE_TEST_NEO4J_URI")
    if not uri:
        pytest.skip("set BEE_TEST_NEO4J_URI for live Neo4j checks")
    with GraphDatabase.driver(uri, auth=None) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            with session.begin_transaction() as transaction:
                workflow_id = uuid4().hex
                transaction.run("CREATE (:Workflow {id: $id})", id=workflow_id).consume()
                yield transaction, workflow_id
                transaction.rollback()


@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("final_state", ["COMPLETED", "RESTARTED", "FAILED"])
def test_zero_input_explicit_readiness(live_graph, reverse_order, final_state):
    """Zero-input tasks become READY only after explicit dependencies finish."""
    transaction, workflow_id = live_graph
    setup = Task(name="setup", base_command=["true"], workflow_id=workflow_id)
    run = Task(name="run", base_command=["true"], workflow_id=workflow_id,
               depends_on=["setup"])
    for task in ([run, setup] if reverse_order else [setup, run]):
        cypher.create_task(transaction, task)
        cypher.add_dependencies(transaction, task)

    cypher.set_runnable_tasks_to_ready(transaction, workflow_id)
    assert cypher.get_task_by_id(transaction, setup.id)["state"] == "READY"
    assert cypher.get_task_by_id(transaction, run.id)["state"] == "WAITING"
    transaction.run("MATCH (t:Task {id: $id}) SET t.state = $state",
                    id=setup.id, state=final_state).consume()
    cypher.set_runnable_tasks_to_ready(transaction, workflow_id)
    assert cypher.get_task_by_id(transaction, run.id)["state"] == "READY"


@pytest.mark.parametrize("command", ["true", ["echo", "one"],
                                     [["echo", "one"], ["echo", "two"]]])
def test_command_roundtrip(live_graph, command):
    """Neo4j storage round-trips legacy and nested commands without type loss."""
    transaction, workflow_id = live_graph
    task = Task(name="command", base_command=command, workflow_id=workflow_id)
    cypher.create_task(transaction, task)
    record = cypher.get_task_by_id(transaction, task.id)
    restored = _reconstruct_task(record, [], [], [], [], {})
    assert restored.base_command == command


def test_explicit_restart_remaps_edge(live_graph):
    """Dependents are linked to the replacement task rather than its old ID."""
    transaction, workflow_id = live_graph
    setup = Task(name="setup", base_command=["true"], workflow_id=workflow_id)
    run = Task(name="run", base_command=["true"], workflow_id=workflow_id,
               depends_on=["setup"])
    for task in [setup, run]:
        cypher.create_task(transaction, task)
        cypher.add_dependencies(transaction, task)
    replacement = setup.copy(update={"new_id": True})
    cypher.create_task(transaction, replacement)
    cypher.add_dependencies(transaction, replacement, old_task=setup, restarted_task=True)
    edges = transaction.run(
        "MATCH (:Task {id: $id})-[r:DEPENDS_ON]->(d:Task) "
        "RETURN d.id AS id, r.explicit AS explicit", id=run.id,
    ).data()
    assert edges == [{"id": replacement.id, "explicit": True}]


@pytest.mark.parametrize("explicit", [None, False, True])
def test_gate_only_applies_to_explicit_edges(live_graph, explicit):
    """Filled inputs retain legacy readiness unless their edge is explicit."""
    transaction, workflow_id = live_graph
    setup = Task(name="setup", base_command=["true"], workflow_id=workflow_id,
                 state="RUNNING")
    run = Task(name="run", base_command=["true"], workflow_id=workflow_id,
               inputs=[StepInput(id="value", type="String", value="filled")])
    for task in [setup, run]:
        cypher.create_task(transaction, task)
        cypher.create_task_input_nodes(transaction, task)
    transaction.run(
        "MATCH (s:Task {id: $setup}), (t:Task {id: $run}) "
        "CREATE (t)-[r:DEPENDS_ON]->(s) SET r.explicit = $explicit",
        setup=setup.id, run=run.id, explicit=explicit,
    ).consume()
    cypher.set_runnable_tasks_to_ready(transaction, workflow_id)
    expected = "WAITING" if explicit else "READY"
    assert cypher.get_task_by_id(transaction, run.id)["state"] == expected


def test_missing_input_still_blocks_readiness(live_graph):
    """The zero-input fix must not release tasks with unfilled input nodes."""
    transaction, workflow_id = live_graph
    task = Task(name="waiting", base_command=["true"], workflow_id=workflow_id,
                inputs=[StepInput(id="missing", type="String")])
    cypher.create_task(transaction, task)
    cypher.create_task_input_nodes(transaction, task)
    cypher.set_runnable_tasks_to_ready(transaction, workflow_id)
    assert cypher.get_task_by_id(transaction, task.id)["state"] == "WAITING"
