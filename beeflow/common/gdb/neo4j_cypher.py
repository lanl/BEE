"""Neo4j/Cypher transaction functions used by the Neo4jDriver class."""


# Is this called? Is it necessary? Tasks have unique IDs.
# What happens if this is set and the assert fails? Where do we catch it?
def constrain_task_names_unique(tx):
    """Constrain tasks to have unique names."""
    unique_query = ("CREATE CONSTRAINT ON (t:Task) "
                    "ASSERT t.name IS UNIQUE")

    tx.run(unique_query)


# How does this file know about the Task class? There is no import.
def create_task_node(tx, task):
    """Create a Task node in the Neo4j database.

    :param task: the new task to create
    :type task: instance of Task
    """
    create_query = ("CREATE (t:Task) "
                    "SET t.task_id = $task_id "
                    "SET t.name = $name "
                    "SET t.command = $command "
                    "SET t.subworkflow = $subworkflow "
                    "SET t.inputs = $inputs "
                    "SET t.outputs = $outputs "
                    "SET t.scatter = $scatter "
                    "SET t.glob = $glob "
                    "SET t.state = 'WAITING'")

    # Unpack requirements, hints dictionaries into flat list
    tx.run(create_query, task_id=task.id, name=task.name,
           command=task.command, subworkflow=task.subworkflow,
           inputs=list(task.inputs), outputs=list(task.outputs),
           scatter=task.scatter, glob=task.glob)


def create_bee_init_node(tx, inputs):
    """Create the bee_init node in the Neo4j database.

    :param inputs: the workflow inputs
    :type inputs: list of strings
    """
    bee_init_query = ("CREATE (t:Task) "
                      "SET t.task_id = '0' "
                      "SET t.name = 'bee_init' "
                      "SET t.inputs = $inputs "
                      "SET t.outputs = $inputs "
                      "SET t.state = 'WAITING'")

    tx.run(bee_init_query, inputs=inputs)


def create_bee_exit_node(tx, outputs):
    """Create the bee_exit node in the Neo4j database.

    :param outputs: the workflow outputs
    :type outputs: list of strings
    """
    bee_exit_query = ("CREATE (t:Task) "
                      "SET t.task_id = '1' "
                      "SET t.name = 'bee_exit' "
                      "SET t.inputs = $outputs "
                      "SET t.outputs = $outputs "
                      "SET t.state = 'WAITING'")

    tx.run(bee_exit_query, outputs=outputs)


def create_workflow_node(tx, workflow):
    """Create a Workflow node in the Neo4j database.

    The workflow node is the entry point to the workflow.

    :param workflow: the workflow description
    :type workflow: instance of Workflow
    """
    workflow_query = ("CREATE (w:Workflow) "
                      "SET w.name = $name "
                      "SET w.inputs = $inputs "
                      "SET w.outputs = $outputs")

    # Store the workflow name, inputs, and outputs, in a new workflow node
    tx.run(workflow_query, name=workflow.name, inputs=workflow.inputs, outputs=workflow.outputs)


def create_task_hint_nodes(tx, task):
    """Create TaskHint nodes for a task.

    :param task: the task whose hints to add to the workflow
    :type task: instance of Task
    """
    hint_query = ("MATCH (t:Task {task_id: $task_id}) "
                  "CREATE (t)-[:HAS_HINT]->(h:TaskHint :Hint) "
                  "SET h.class = $req_class "
                  "SET h.key = $key "
                  "SET h.value = $value")

    for hint in task.hints:
        tx.run(hint_query, task_id=task.id, req_class=hint.req_class, key=hint.key,
               value=hint.value)


def create_task_requirement_nodes(tx, task):
    """Create TaskRequirement nodes for a task.

    :param task: the task whose requirements to add to the workflow
    :type task: instance of Task
    """
    req_query = ("MATCH (t:Task {task_id: $task_id}) "
                 "CREATE (t)-[:HAS_REQUIREMENT]->(r:TaskRequirement :Requirement) "
                 "SET r.class = $req_class "
                 "SET r.key = $key "
                 "SET r.value = $value")

    for hint in task.hints:
        tx.run(req_query, task_id=task.id, req_class=hint.req_class, key=hint.key,
               value=hint.value)


def create_workflow_hint_nodes(tx, hints):
    """Create WorkflowHint nodes for the workflow.

    :param hints: the workflow hints
    :type hints: list of Requirement instances
    """
    hint_query = ("MATCH (w:Workflow) "
                  "CREATE (w)-[:HAS_HINT]->(h:WorkflowHint :Hint) "
                  "SET h.class = $req_class "
                  "SET h.key = $key "
                  "SET h.value = $value")

    for hint in hints:
        tx.run(hint_query, req_class=hint.req_class, key=hint.key, value=hint.value)


def create_workflow_requirement_nodes(tx, requirements):
    """Create WorkflowHint and WorkflowRequirement nodes for the workflow.

    :param requirements: the workflow requirements
    :type requirements: list of Requirement instances
    """
    req_query = ("MATCH (w:Workflow) "
                 "CREATE (w)-[:HAS_HINT]->(r:WorkflowRequirement :Requirement) "
                 "SET r.class = $req_class "
                 "SET r.key = $key "
                 "SET r.value = $value")

    for req in requirements:
        tx.run(req_query, req_class=req.req_class, key=req.key, value=req.value)


def add_dependencies(tx, task):
    """Create dependencies between tasks.

    :param task: the workflow task
    :type task: instance of Task
    """
    dependency_query = ("MATCH (s:Task {task_id: $task_id}), (t:Task) "
                        "WHERE ANY(input in s.inputs WHERE input in t.outputs) "
                        "AND NOT (s)-[:DEPENDS]->(t) "
                        "CREATE (s)-[:DEPENDS]->(t) "
                        "WITH s "
                        "MATCH (t:Task) "
                        "WHERE ANY(output in s.outputs WHERE output in t.inputs) "
                        "AND NOT (t)-[:DEPENDS]->(s) "
                        "CREATE (t)-[:DEPENDS]->(s)")

    tx.run(dependency_query, task_id=task.id)


def delete_task_node(tx, task):
    """Delete the specified task node in the Neo4j database.

    :param task: the workflow task
    :type task: instance of Task
    """
    delete_query = "MATCH (t:Task {task_id: $task_id}) DETACH DELETE t"

    tx.run(delete_query, task_id=task.id)


def delete_input_dependencies(tx, task):
    """Delete the input dependency relationships of a task in the Neo4j database.

    :param task: the workflow task
    :type task: instance of Task
    """
    delete_query = "MATCH (:Task)<-[d:DEPENDS]-(:Task {task_id: $task_id}) DELETE d"

    tx.run(delete_query, task_id=task.id)


def delete_output_dependencies(tx, task):
    """Delete the output dependency relationships of a task in the Neo4j database.

    :param task: the workflow task
    :type task: instance of Task
    """
    delete_query = "MATCH (:Task {task_id: $task_id})<-[d:DEPENDS]-(:Task) DELETE d"

    tx.run(delete_query, task_id=task.id)


def get_task_by_id(tx, task_id):
    """Get a workflow task from the Neo4j database by its ID.

    :param task_id: the task's ID
    :type task_id: str
    """
    task_query = "MATCH (t:Task {task_id: $task_id}) RETURN t"

    return tx.run(task_query, task_id=task_id).single()


def get_workflow_tasks(tx):
    """Get workflow tasks from the Neo4j database."""
    workflow_query = "MATCH (t:Task) RETURN t"

    return tx.run(workflow_query)


def get_task_hints(tx, task):
    """Get hints for a task from the Neo4j database."""
    hints_query = "MATCH (:Task {task_id: $task_id})-[:HAS_HINT]->(r:TaskHint) RETURN r"

    return tx.run(hints_query, task_id=task.id)


def get_task_requirements(tx, task):
    """Get requirements for a task from the Neo4j database."""
    req_query = ("MATCH (:Task {task_id: $task_id})-[:HAS_REQUIREMENT]->(r:TaskRequirement) "
                 "RETURN r")

    return tx.run(req_query, task_id=task.id)


def get_workflow_hints(tx):
    """Get workflow hints from the Neo4j database."""
    hints_query = "MATCH (:Workflow)-[:HAS_HINT]->(r:WorkflowHint) RETURN r"

    return tx.run(hints_query)


def get_workflow_requirements(tx):
    """Get workflow requirements from the Neo4j database."""
    req_query = "MATCH (:Workflow)-[:HAS_REQUIREMENT]->(r:WorkflowRequirement) RETURN r"

    return tx.run(req_query)


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


def set_task_inputs(tx, task, inputs):
    """Set a task's inputs.

    :param task: the task whose inputs to change
    :type task: instance of Task
    :param inputs: the new task inputs
    :type inputs: list of strings
    """
    state_query = ("MATCH (t:Task {task_id: $task_id}) "
                   "SET t.inputs = $inputs")

    tx.run(state_query, task_id=task.id, inputs=inputs)


def set_task_outputs(tx, task, outputs):
    """Set a task's outputs.

    :param task: the task whose outputs to change
    :type task: instance of Task
    :param outputs: the new task state
    :type outputs: string
    """
    state_query = ("MATCH (t:Task {task_id: $task_id}) "
                   "SET t.outputs = $outputs")

    tx.run(state_query, task_id=task.id, outputs=outputs)


def is_empty(tx):
    """Return true if the database is empty, else false."""
    empty_query = "MATCH (t:Task) RETURN t IS NULL LIMIT 1"

    return tx.run(empty_query).single()


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = "MATCH (n) DETACH DELETE n"

    tx.run(cleanup_query)
