"""Neo4j/Cypher transaction functions used by the Neo4jDriver class."""


def constrain_task_names_unique(tx):
    """Constrain tasks to have unique names."""
    unique_query = ("CREATE CONSTRAINT ON (t:Task) "
                    "ASSERT t.name IS UNIQUE")

    tx.run(unique_query)


def create_task(tx, task):
    """Create a Task node in the Neo4j database.

    :param task: the new task to create
    :type task: instance of Task
    """
    create_query = ("CREATE (t:Task) "
                    "SET t.task_id = $task_id "
                    "SET t.name = $name "
                    "SET t.command = $command "
                    "SET t.hints = $hints "
                    "SET t.dependencies = $dependencies "
                    "SET t.subworkflow = $subworkflow "
                    "SET t.inputs = $inputs "
                    "SET t.outputs = $outputs "
                    "SET t.state = 'WAITING'")

    # Unpack requirements, hints dictionaries into flat list
    tx.run(create_query, task_id=task.id, name=task.name,
           command=task.command, hints=_encode_requirements(task.hints),
           dependencies=list(task.dependencies), subworkflow=task.subworkflow,
           inputs=list(task.inputs), outputs=list(task.outputs))


def create_metadata_node(tx, requirements, hints):
    """Create a metadata node in the Neo4j database.

    The metadata node holds the workflow requirements and hints.
    :param requirements: the workflow requirements
    :type requirements: set of Requirement instances
    :param hints: the workflow hints
    :type hints: set of Requirement instances
    """
    metadata_query = "CREATE (n:Metadata {requirements: $requirements, hints: $hints})"

    # Store the workflow requirements and hints in a metadata node
    tx.run(metadata_query, requirements=_encode_requirements(requirements),
           hints=_encode_requirements(hints))


def add_dependencies(tx, task):
    """Create a dependency between two tasks.

    :param task: the task whose dependencies to add
    :type task: instance of Task
    """
    dependency_query = ("MATCH (s:Task), (t:Task) "
                        "WHERE s.task_id = $dependent_id and t.task_id = $dependency_id "
                        "CREATE (s)-[:DEPENDS]->(t)")

    for dependency_id in task.dependencies:
        tx.run(dependency_query, dependent_id=task.id, dependency_id=dependency_id)


def get_workflow_tasks(tx):
    """Get workflow tasks from the Neo4j database."""
    workflow_query = "MATCH (t:Task) RETURN t"

    return tx.run(workflow_query)


def get_workflow_requirements(tx):
    """Get workflow requirements from the Neo4j database."""
    requirements_query = "MATCH (n:Metadata) RETURN n.requirements"

    return tx.run(requirements_query).single().value()


def get_workflow_hints(tx):
    """Get workflow hints from the Neo4j database."""
    hints_query = "MATCH (n:Metadata) RETURN n.hints"

    return tx.run(hints_query).single().value()


def get_subworkflow_tasks(tx, subworkflow):
    """Get subworkflow tasks from the Neo4j database with the specified identifier.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: BoltStatementResult
    """
    subworkflow_query = "MATCH (t:Task {subworkflow: $subworkflow}) RETURN t"

    return tx.run(subworkflow_query, subworkflow=subworkflow)


def get_dependent_tasks(tx, task):
    """Get the tasks that depend on a specified task.

    :param task: the task whose dependencies to obtain
    :type task: instance of Task
    """
    dependents_query = "MATCH (t:Task)-[:DEPENDS]->(s:Task {task_id: $task_id})  RETURN t"

    return tx.run(dependents_query, task_id=task.id)


def get_task_id_by_name(tx, task):
    """Get the ID of a task.

    :param task: the task whose ID to get
    :type task: instance of Task
    """
    id_query = "MATCH (t:Task {name: $name}) RETURN t.task_id"

    return tx.run(id_query, name=task.name).single().value()


def get_task_state(tx, task):
    """Get the state of a task.

    :param task: the task whose state to get
    :type task: instance of Task
    """
    state_query = "MATCH (t:Task {task_id: $task_id}) RETURN t.state"

    return tx.run(state_query, task_id=task.id).single().value()


def get_head_task_names(tx):
    """Return all tasks with no dependencies."""
    start_task_query = ("MATCH (t:Task) WHERE NOT (t)-[:DEPENDS]->() "
                        "RETURN collect(t.name)")

    return tx.run(start_task_query).single().value()


def get_tail_task_names(tx):
    """Return all tasks with no dependents."""
    end_task_query = ("MATCH (t:Task) WHERE NOT (t)<-[:DEPENDS]-() "
                      "RETURN collect(t.name)")

    return tx.run(end_task_query).single().value()


def set_init_task_to_ready(tx):
    """Set bee_init's state to READY."""
    init_ready_query = ("MATCH (t:Task {name: 'bee_init'}) "
                        "SET t.state = 'READY'")

    tx.run(init_ready_query)


def set_exit_task_to_ready(tx):
    """Set bee_exit's state to READY."""
    exit_ready_query = ("MATCH (t:Task {name: 'bee_exit'}) "
                        "SET t.state = 'READY'")

    tx.run(exit_ready_query)


def set_task_state(tx, task, state):
    """Set a task's state.

    :param task: the task whose state to change
    :type task: instance of Task
    :param state: the new task state
    :type state: string
    """
    state_query = ("MATCH (t:Task {task_id: $task_id}) "
                   "SET t.state = $state")

    tx.run(state_query, task_id=task.id, state=state)


def is_empty(tx):
    """Return true if the database is empty, else false."""
    empty_query = "MATCH (t:Task) RETURN t IS NULL LIMIT 1"

    return tx.run(empty_query).single()


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = "MATCH (n) DETACH DELETE n"

    tx.run(cleanup_query)


def _encode_requirements(reqs):
    """Encode requirements as a flat list of ordered class-key-value triplets as strings.

    :param reqs: the requirements to encode
    :type reqs: iterable of Requirement instances
    """
    return [str(prop) for req in reqs for prop in req]
