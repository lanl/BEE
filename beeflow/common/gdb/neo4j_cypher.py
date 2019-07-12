"""Neo4j/Cypher transaction functions used by the Neo4jDriver class."""


def constrain_tasks_unique(tx):
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
                    "SET t.subworkflow = $subworkflow")

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


def get_subworkflow(tx, subworkflow):
    """Get subworkflows from the Neo4j database with the specified head tasks.

    :param subworkflow: the head tasks of the subworkflows
    :type subworkflow: list of Task instances
    :rtype: instance of Workflow
    """
    subworkflow_query = ("MATCH (t:Task {subworkflow: $subworkflow}) "
                         "RETURN collect(t.task_id)")

    return tx.run(subworkflow_query, subworkflow=subworkflow).values()


def set_head_tasks_to_ready(tx):
    """Initialize the workflow by setting the head tasks" state to READY."""
    ready_query = ("MATCH (t:Task) WHERE NOT (t)-[:DEPENDS]->() "
                   "SET t.state = 'READY'")

    tx.run(ready_query)


def set_ready_tasks_to_running(tx):
    """Set all tasks with state READY to RUNNING."""
    running_query = ("MATCH (t:Task {state: 'READY'}) "
                     "SET t.state = 'RUNNING'")

    tx.run(running_query)


def set_task_to_complete(tx, task):
    """Set a task with state RUNNING to COMPLETE.

    :param task: the task whose state to change to COMPLETE
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

    return tx.run(dependents_query, task_id=task.id).values()


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


def cleanup(tx):
    """Clean up all workflow data in the database."""
    cleanup_query = ("MATCH (n) WITH n LIMIT 10000 "
                     "DETACH DELETE n")

    tx.run(cleanup_query)
