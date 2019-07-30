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
                    "SET t.commands = $commands "
                    "SET t.requirements = $requirements "
                    "SET t.hints = $hints "
                    "SET t.dependencies = $dependencies "
                    "SET t.subworkflow = $subworkflow "
                    "SET t.inputs = $inputs "
                    "SET t.outputs = $outputs "
                    "SET t.state = 'WAITING'")

    # Unpack requirements, hints dictionaries into flat list
    tx.run(create_query, task_id=task.id, name=task.name,
           commands=_encode_commands_list(task.commands),
           requirements=_encode_dict_as_list(task.requirements),
           hints=_encode_dict_as_list(task.hints), dependencies=list(task.dependencies),
           subworkflow=task.subworkflow, inputs=list(task.inputs), outputs=list(task.outputs))


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


def get_subworkflow_tasks(tx, subworkflow):
    """Get subworkflows from the Neo4j database with the specified head tasks.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: instance of Workflow
    """
    subworkflow_query = "MATCH (t:Task {subworkflow: $subworkflow}) RETURN t"

    return tx.run(subworkflow_query, subworkflow=subworkflow)


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


def is_empty(tx):
    """Return true if the database is empty, else false."""
    empty_query = "MATCH (t:Task) RETURN t IS NULL LIMIT 1"

    return tx.run(empty_query).single()


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = "MATCH (n) DETACH DELETE n"

    tx.run(cleanup_query)


def _encode_commands_list(commands):
    """Encode the nested list of commands as a flat list.

    :param commands: the list of commands
    :type commands: list of lists of strings
    """
    if not commands:
        return commands

    encoded_list = []
    for command in commands[:-1]:
        encoded_list.extend(c for c in command + [";"])
    encoded_list.extend(c for c in commands[-1])
    return encoded_list


def _encode_dict_as_list(dict_):
    """Encode a dictionary as a flat list of ordered key-value pairs as strings.

    :param dict_: the dictionary to encode
    :type dict_: dictionary
    """
    return [str(k_or_v) for pair in dict_.items() for k_or_v in pair]
