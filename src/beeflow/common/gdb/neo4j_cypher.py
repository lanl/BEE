"""Neo4j/Cypher transaction functions used by the Neo4jDriver class."""


def constrain_workflow_unique(tx):
    """Constrain workflows and tasks to have unique IDs."""
    unique_task_query = ("CREATE CONSTRAINT ON (t:Task) "
                         "ASSERT t.task_id IS UNIQUE")
    unique_workflow_query = ("CREATE CONSTRAINT ON (w:Workflow) "
                             "ASSERT w.workflow_id IS UNIQUE")

    tx.run(unique_task_query)
    tx.run(unique_workflow_query)


def create_workflow_node(tx, workflow):
    """Create a Workflow node in the Neo4j database.

    The workflow node is the entry point to the workflow.
    :param workflow: the workflow description
    :type workflow: Workflow
    """
    workflow_query = ("CREATE (w:Workflow) "
                      "SET w.workflow_id = $workflow_id "
                      "SET w.name = $name "
                      "SET w.inputs = $inputs "
                      "SET w.outputs = $outputs")

    # Store the workflow name, inputs, and outputs, in a new workflow node
    tx.run(workflow_query, workflow_id=workflow.id, name=workflow.name,
           inputs=list(workflow.inputs), outputs=list(workflow.outputs))


def create_workflow_hint_nodes(tx, hints):
    """Create Hint nodes for the workflow.

    :param hints: the workflow hints
    :type hints: set of Hint
    """
    hint_query = ("MATCH (w:Workflow) "
                  "CREATE (w)-[:HAS_HINT]->(h:Hint) "
                  "SET h.class = $class_ "
                  "SET h.key = $key "
                  "SET h.value = $value")

    for hint in hints:
        tx.run(hint_query, class_=hint.class_, key=hint.key, value=hint.value)


def create_workflow_requirement_nodes(tx, requirements):
    """Create Requirement nodes for the workflow.

    :param requirements: the workflow requirements
    :type requirements: set of Requirement
    """
    req_query = ("MATCH (w:Workflow) "
                 "CREATE (w)-[:HAS_REQUIREMENT]->(r:Requirement) "
                 "SET r.class = $class_ "
                 "SET r.key = $key "
                 "SET r.value = $value")

    for req in requirements:
        tx.run(req_query, class_=req.class_, key=req.key, value=req.value)


def create_task(tx, task):
    """Create a Task node in the Neo4j database.

    :param task: the new task to create
    :type task: Task
    """
    create_query = ("CREATE (t:Task) "
                    "SET t.task_id = $task_id "
                    "SET t.workflow_id = $workflow_id "
                    "SET t.name = $name "
                    "SET t.command = $command "
                    "SET t.subworkflow = $subworkflow "
                    "SET t.inputs = $inputs "
                    "SET t.outputs = $outputs ")

    # Unpack requirements, hints dictionaries into flat list
    tx.run(create_query, task_id=task.id, workflow_id=task.workflow_id, name=task.name,
           command=task.command, subworkflow=task.subworkflow, inputs=list(task.inputs),
           outputs=list(task.outputs))


def create_task_hint_nodes(tx, task):
    """Create Hint nodes for a task.

    :param task: the task whose hints to add to the graph
    :type task: Task
    """
    hint_query = ("MATCH (t:Task {task_id: $task_id}) "
                  "CREATE (t)-[:HAS_HINT]->(h:Hint) "
                  "SET h.class = $class_ "
                  "SET h.key = $key "
                  "SET h.value = $value")

    for hint in task.hints:
        tx.run(hint_query, task_id=task.id, class_=hint.class_, key=hint.key, value=hint.value)


def create_task_requirement_nodes(tx, task):
    """Create Requirement nodes for a task.

    :param task: the task whose requirements to add to the graph
    :type task: Task
    """
    req_query = ("MATCH (t:Task {task_id: $task_id}) "
                 "CREATE (t)-[:HAS_REQUIREMENT]->(h:Requirement) "
                 "SET h.class = $class_ "
                 "SET h.key = $key "
                 "SET h.value = $value")

    for req in task.requirements:
        tx.run(req_query, task_id=task.id, class_=req.class_, key=req.key, value=req.value)


def create_task_metadata_node(tx, task):
    """Create a task metadata node in the Neo4j database.

    The node holds metadata about a task's execution state.

    :param task: the task for which to create a metadata node
    :type task: Task
    """
    metadata_query = ("MATCH (t:Task {task_id: $task_id}) "
                      "CREATE (m:Metadata {state: 'WAITING'})-[:DESCRIBES]->(t)")

    tx.run(metadata_query, task_id=task.id)


def add_dependencies(tx, task):
    """Create dependencies between tasks.

    :param task: the workflow task
    :type task: Task
    """
    begins_query = ("MATCH (s:Task {task_id: $task_id}), (w:Workflow) "
                    "WHERE any(input IN s.inputs WHERE input IN w.inputs) "
                    "MERGE (s)-[:BEGINS]->(w)")
    dependency_query = ("MATCH (s:Task {task_id: $task_id}), (t:Task) "
                        "WHERE any(input IN s.inputs WHERE input IN t.outputs) "
                        "MERGE (s)-[:DEPENDS]->(t) "
                        "WITH s "
                        "MATCH (t:Task) "
                        "WHERE any(output IN s.outputs WHERE output IN t.inputs) "
                        "MERGE (t)-[:DEPENDS]->(s)")

    tx.run(begins_query, task_id=task.id)
    tx.run(dependency_query, task_id=task.id)


def get_task_by_id(tx, task_id):
    """Get a workflow task from the Neo4j database by its ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    task_query = "MATCH (t:Task {task_id: $task_id}) RETURN t"

    return tx.run(task_query, task_id=task_id).single()


def get_task_hints(tx, task_id):
    """Get task hints from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    hints_query = "MATCH (:Task {task_id: $task_id})-[:HAS_HINT]->(h:Hint) RETURN h"

    return tx.run(hints_query, task_id=task_id)


def get_task_requirements(tx, task_id):
    """Get task requirements from the Neo4j database by the task's ID.

    :param task_id: the task's ID
    :type task_id: str
    :rtype: BoltStatementResult
    """
    reqs_query = "MATCH (:Task {task_id: $task_id})-[:HAS_REQUIREMENT]->(r:Requirement) RETURN r"

    return tx.run(reqs_query, task_id=task_id)


def get_workflow_description(tx):
    """Get the workflow description from the Neo4j database.

    :rtype: BoltStatementResult
    """
    workflow_desc_query = "MATCH (w:Workflow) RETURN w"

    return tx.run(workflow_desc_query).single()


def get_workflow_tasks(tx):
    """Get workflow tasks from the Neo4j database.

    :rtype: BoltStatementResult
    """
    workflow_query = "MATCH (t:Task) RETURN t"

    return tx.run(workflow_query)


def get_workflow_requirements(tx):
    """Get workflow requirements from the Neo4j database.

    :rtype: BoltStatementResult
    """
    requirements_query = "MATCH (:Workflow)-[:HAS_REQUIREMENT]->(r:Requirement) RETURN r"

    return tx.run(requirements_query)


def get_workflow_hints(tx):
    """Get workflow hints from the Neo4j database.

    :rtype: BoltStatementResult
    """
    hints_query = "MATCH (:Workflow)-[:HAS_HINT]->(h:Hint) RETURN h"

    return tx.run(hints_query)


def get_ready_tasks(tx):
    """Get all tasks that are ready to execute.

    :rtype: BoltStatementResult
    """
    get_ready_query = "MATCH (:Metadata {state: 'READY'})-[:DESCRIBES]->(t:Task) RETURN t"

    return tx.run(get_ready_query)


def get_subworkflow_tasks(tx, subworkflow):
    """Get subworkflow tasks from the Neo4j database with the specified identifier.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: str
    :rtype: BoltStatementResult
    """
    subworkflow_query = "MATCH (t:Task {subworkflow: $subworkflow}) RETURN t"

    return tx.run(subworkflow_query, subworkflow=subworkflow)


def get_dependent_tasks(tx, task):
    """Get the tasks that depend on a specified task.

    :param task: the task whose dependencies to obtain
    :type task: Task
    :rtype: BoltStatementResult
    """
    dependents_query = "MATCH (t:Task)-[:DEPENDS]->(:Task {task_id: $task_id}) RETURN t"

    return tx.run(dependents_query, task_id=task.id)


def get_task_state(tx, task):
    """Get the state of a task.

    :param task: the task whose state to get
    :type task: Task
    :rtype: str
    """
    state_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {task_id: $task_id}) RETURN m.state"

    return tx.run(state_query, task_id=task.id).single().value()


def set_task_state(tx, task, state):
    """Set a task's state.

    :param task: the task whose state to set
    :type task: Task
    :param state: the new task state
    :type state: str
    """
    state_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(:Task {task_id: $task_id}) "
                   "SET m.state = $state")

    tx.run(state_query, task_id=task.id, state=state)


def get_task_metadata(tx, task):
    """Get a task's metadata.

    :param task: the task whose metadata to get
    :type task: Task
    :rtype: BoltStatementResult
    """
    metadata_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {task_id: $task_id}) RETURN m"

    return tx.run(metadata_query, task_id=task.id).single()


def set_task_metadata(tx, task, metadata):
    """Set a task's metadata.

    :param task: the task whose metadata to set
    :type task: Task
    :param metadata: the task metadata
    :type metadata: dict
    """
    metadata_query = "MATCH (m:Metadata)-[:DESCRIBES]->(:Task {task_id: $task_id})"

    for key, val in metadata.items():
        if isinstance(val, str):
            metadata_query += f" SET m.{key} = '{val}'"
        else:
            metadata_query += f" SET m.{key} = {val}"

    tx.run(metadata_query, task_id=task.id)


def set_init_tasks_to_ready(tx):
    """Set the initial workflow tasks' states to 'READY'."""
    init_ready_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task)-[:BEGINS]->(:Workflow) "
                        "WHERE NOT (t)-[:DEPENDS]->(:Task) "
                        "SET m.state = 'READY'")

    tx.run(init_ready_query)


def set_running_tasks_to_paused(tx):
    """Set 'RUNNING' task states to 'PAUSED'."""
    set_paused_query = ("MATCH (m:Metadata {state: 'RUNNING'})-[:DESCRIBES]->(:Task) "
                        "SET m.state = 'PAUSED'")

    tx.run(set_paused_query)


def set_paused_tasks_to_running(tx):
    """Set 'PAUSED' task states to 'RUNNING'."""
    set_running_query = ("MATCH (m:Metadata {state: 'PAUSED'})-[:DESCRIBES]->(:Task) "
                         "SET m.state = 'RUNNING'")

    tx.run(set_running_query)


def set_runnable_tasks_to_ready(tx):
    """Set task states to 'READY' if all dependencies have state 'COMPLETED'."""
    set_runnable_ready_query = ("MATCH (t:Task)-[:DEPENDS]->(s:Task)<-[:DESCRIBES]-(m:Metadata) "
                                "WITH t, collect(m) AS mlist "
                                "WHERE all(m IN mlist WHERE m.state = 'COMPLETED') "
                                "MATCH (m:Metadata)-[:DESCRIBES]->(t) "
                                "WHERE m.state = 'WAITING' "
                                "SET m.state = 'READY'")

    tx.run(set_runnable_ready_query)


def reset_tasks_metadata(tx):
    """Reset the metadata for each of a workflow's tasks."""
    reset_metadata_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task) "
                            "DETACH DELETE m "
                            "WITH t "
                            "CREATE (:Metadata {state: 'WAITING'})-[:DESCRIBES]->(t)")

    tx.run(reset_metadata_query)


def reset_workflow_id(tx, new_id):
    """Reset the workflow ID of the workflow using uuid4.

    :param new_id: the new workflow ID
    :type new_id: str
    """
    reset_workflow_id_query = ("MATCH (w:Workflow), (t:Task) "
                               "SET w.workflow_id = $new_id "
                               "SET t.workflow_id = $new_id")

    tx.run(reset_workflow_id_query, new_id=new_id)


def all_tasks_completed(tx):
    """Return true if all of a workflow's tasks have state 'COMPLETED'.

    :rtype: bool
    """
    not_completed_query = ("MATCH (m:Metadata)-[:DESCRIBES]->(t:Task) "
                           "WHERE m.state <> 'COMPLETED' "
                           "RETURN t IS NOT NULL LIMIT 1")

    # False if at least one task with state not 'COMPLETED'
    return bool(tx.run(not_completed_query).single() is None)


def is_empty(tx):
    """Return true if the database is empty, else false.

    :rtype: bool
    """
    empty_query = "MATCH (n) RETURN n IS NULL LIMIT 1"

    # False if at least one task
    return bool(tx.run(empty_query).single() is None)


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = "MATCH (n) DETACH DELETE n"

    tx.run(cleanup_query)
