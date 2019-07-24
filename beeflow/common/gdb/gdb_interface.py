"""Mid-level interface for managing a graph database with workflows.

Delegates the actual work to an instance of a subclass of
the abstract base class `GraphDatabaseDriver`. By default,
this is the `Neo4jDriver` class.
"""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver

_GDB_DRIVER = None


def connect(gdb_driver=Neo4jDriver, **kwargs):
    """Initialize a graph database interface with a driver.

    :param gdb_driver: the graph database driver (Neo4jDriver by default)
    :type gdb_driver: subclass of GraphDatabaseDriver
    :param kwargs: optional arguments for the graph database driver
    """
    global _GDB_DRIVER
    _GDB_DRIVER = gdb_driver(**kwargs)


def load_workflow(workflow):
    """Load a BEE workflow into the graph database.

    :param workflow: the new workflow to load
    :type workflow: instance of Workflow
    """
    _GDB_DRIVER.load_workflow(workflow)

    # Get head and tail tasks
    head_task_names = _GDB_DRIVER.get_head_task_names()
    tail_task_names = _GDB_DRIVER.get_tail_task_names()

    # Add a bee_init node if there is none
    if _no_init_node(head_task_names):
        _GDB_DRIVER.add_init_node()

    # Add a bee_exit node if there is none
    if _no_exit_node(tail_task_names):
        _GDB_DRIVER.add_exit_node()


def get_subworkflow_ids(subworkflow):
    """Return a subworkflows' task IDs from the graph database.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: list of integers
    """
    return _GDB_DRIVER.get_subworkflow_ids(subworkflow)


def initialize_workflow():
    """Start the workflow loaded into the graph database."""
    _GDB_DRIVER.initialize_workflow()


def get_dependent_tasks(task):
    """Return the dependents of a task in a graph database workflow.

    :param task: the task whose dependents to retrieve
    :type task: instance of Task
    :rtype: set of Task instances
    """
    return _GDB_DRIVER.get_dependent_tasks(task)


def get_task_state(task):
    """Return the state of a task in a graph database workflow.

    :param task: the task whose state to retrieve
    :type task: instance of Task
    :rtype: string
    """
    return _GDB_DRIVER.get_task_state(task)


def finalize_workflow():
    """Finalize the workflow loaded into the graph database."""
    _GDB_DRIVER.finalize_workflow()


def _no_init_node(head_tasks):
    """Determine if there is no bee_init node.

    :param head_tasks: the names of the head tasks
    :type head_tasks: list of strings
    """
    return not bool(len(head_tasks) == 1 and head_tasks[0] == "bee_init")


def _no_exit_node(tail_tasks):
    """Determine if there is no bee_exit node.

    :param tail_tasks: the names of the tail tasks
    :type tail_tasks: list of strings
    """
    return not bool(len(tail_tasks) == 1 and tail_tasks[0] == "bee_exit")
