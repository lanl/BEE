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
                    "SET t.base_command = $base_command "
                    "SET t.arguments = $arguments "
                    "SET t.dependencies = $dependencies "
                    "SET t.subworkflow = $subworkflow "
                    "SET t.state = 'WAITING'")

    tx.run(create_query, task_id=task.id, name=task.name, base_command=task.base_command,
           arguments=task.arguments, dependencies=list(task.dependencies),
           subworkflow=task.subworkflow)


def add_dependencies(tx, task):
    """Create a dependency between two tasks.

    :param task: the task whose dependencies to add
    :type task: instance of Task
    """
    dependency_query = ("MATCH (s:Task), (t:Task) "
                        "WHERE s.name = $dependent_name and t.name = $dependency_name "
                        "CREATE (s)-[:DEPENDS]->(t)")

    for dependency in task.dependencies:
        tx.run(dependency_query, dependent_name=task.name, dependency_name=dependency)


def get_subworkflow_ids(tx, subworkflow):
    """Get subworkflows from the Neo4j database with the specified head tasks.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: instance of Workflow
    """
    subworkflow_query = ("MATCH (t:Task {subworkflow: $subworkflow}) "
                         "RETURN collect(t.task_id)")

    return tx.run(subworkflow_query, subworkflow=subworkflow).single().value()


def create_init_node(tx):
    """Create a task node with the name 'bee_init' and state 'WAITING'."""
    init_node_query = ("CREATE (s:Task {name: 'bee_init', task_id: 0, state: 'WAITING'}) "
                       "WITH s "
                       "MATCH (t:Task) WHERE NOT (t)-[:DEPENDS]->() AND NOT t.name = 'bee_init' "
                       "CREATE (s)<-[:DEPENDS]-(t)")

    tx.run(init_node_query)


def create_exit_node(tx):
    """Create a task node with the name 'bee_exit' and state 'WAITING'."""
    exit_node_query = ("MATCH (n:Task) "
                       "WITH max(n.task_id) + 1 AS task_id "
                       "CREATE (s:Task {name: 'bee_exit', task_id: task_id, state: 'WAITING'}) "
                       "WITH s "
                       "MATCH (t:Task) WHERE NOT (t)<-[:DEPENDS]-() AND NOT t.name = 'bee_exit' "
                       "CREATE (s)-[:DEPENDS]->(t)")

    tx.run(exit_node_query)


def set_init_task_to_ready(tx):
    """Set bee_init's state to READY."""
    init_ready_query = ("MATCH (t:Task {task_id: 'bee_init'}) "
                        "SET t.state = 'READY'")

    tx.run(init_ready_query)


def set_exit_task_to_ready(tx):
    """Set bee_exit's state to READY."""
    exit_ready_query = ("MATCH (t:Task {name: 'bee_exit'}) "
                        "SET t.state = 'READY'")

    tx.run(exit_ready_query)


def set_task_to_ready(tx, task):
    """Set a task's state to READY.

    :param task: the task whose state to change
    :type task: instance of Task
    """
    ready_query = ("MATCH (t:Task {task_id: $task_id}) "
                   "SET t.state = 'READY'")

    tx.run(ready_query, task_id=task.id)


def set_task_to_running(tx, task):
    """Set a task's state to RUNNING.

    :param task: the task whose state to change
    :type task: instance of Task
    """
    running_query = ("MATCH (t:Task {task_id: $task_id}) "
                     "SET t.state = 'RUNNING'")

    tx.run(running_query, task_id=task.id)


def set_task_to_complete(tx, task):
    """Set a task's state to COMPLETE.

    :param task: the task whose state to change
    :type task: instance of Task
    """
    complete_query = ("MATCH (t:Task {task_id: $task_id}) "
                      "SET t.state = 'COMPLETE'")

    tx.run(complete_query, task_id=task.id)


def set_task_to_failed(tx, task):
    """Set a task with state RUNNING to FAILED.

    :param task: the task whose state to change to FAILED
    :type task: instance of Task
    """
    failed_query = ("MATCH (t:Task {task_id: $task_id}) "
                    "SET t.state = 'FAILED'")

    tx.run(failed_query, task_id=task.id)


def get_dependent_tasks(tx, task):
    """Get the tasks that depend on a specified task.

    :param task: the task whose dependencies to obtain
    :type task: instance of Task
    """
    dependents_query = ("MATCH (t:Task)-[:DEPENDS]->(s:Task {task_id: $task_id}) "
                        "RETURN collect(t.task_id)")

    return tx.run(dependents_query, task_id=task.id).single().value()


def get_task_id_by_name(tx, task):
    """Get the ID of a task.

    :param task: the task whose ID to get
    :type task: instance of Task
    """
    id_query = ("MATCH (t:Task {name: $name}) "
                "RETURN t.task_id")

    return tx.run(id_query, name=task.name).single().value()


def get_task_state(tx, task):
    """Get the state of a task.

    :param task: the task whose state to get
    :type task: instance of Task
    """
    state_query = ("MATCH (t:Task {task_id: $task_id}) "
                   "RETURN t.state")

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


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = ("MATCH (n) WITH n LIMIT 10000 "
                     "DETACH DELETE n")

    tx.run(cleanup_query)
