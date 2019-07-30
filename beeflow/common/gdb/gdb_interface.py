"""Mid-level interface for managing a graph database with workflows.

Delegates the actual work to an instance of a subclass of
the abstract base class `GraphDatabaseDriver`. By default,
this is the `Neo4jDriver` class.
"""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver

# Store the GDB driver state
_GDB_DRIVER = None


def connect(gdb_driver=Neo4jDriver, **kwargs):
    """Initialize a graph database interface with a driver.

    :param gdb_driver: the graph database driver (Neo4jDriver by default)
    :type gdb_driver: subclass of GraphDatabaseDriver
    :param kwargs: optional arguments for the graph database driver
    """
    # Initialize the graph database driver
    global _GDB_DRIVER
    _GDB_DRIVER = gdb_driver(**kwargs)


def load_workflow(workflow):
    """Load a BEE workflow into the graph database.

    :param workflow: the new workflow to load
    :type workflow: instance of Workflow
    """
    # Load the workflow into the graph database
    _GDB_DRIVER.load_workflow(workflow)


def initialize_workflow():
    """Start the workflow loaded into the graph database."""
    _GDB_DRIVER.initialize_workflow()


def finalize_workflow():
    """Finalize the workflow loaded into the graph database."""
    _GDB_DRIVER.finalize_workflow()


def get_subworkflow_tasks(subworkflow):
    """Return a subworkflow's Task objects from the graph database.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: list of Task instances
    """
    task_records = _GDB_DRIVER.get_subworkflow_tasks(subworkflow)
    return [_GDB_DRIVER.reconstruct_task(task_record) for task_record in task_records]


def get_dependent_tasks(task):
    """Return the dependents of a task in a graph database workflow.

    :param task: the task whose dependents to retrieve
    :type task: instance of Task
    :rtype: set of Task instances
    """
    task_records = _GDB_DRIVER.get_dependent_tasks(task)
    return {_GDB_DRIVER.reconstruct_task(task_record) for task_record in task_records}


def get_task_state(task):
    """Return the state of a task in a graph database workflow.

    :param task: the task whose state to retrieve
    :type task: instance of Task
    :rtype: string
    """
    return _GDB_DRIVER.get_task_state(task)


def empty():
    """Return true if the graph database is empty, else false.

    :rtype: boolean
    """
    return _GDB_DRIVER.empty()


def _no_init_node(head_tasks):
    """Determine if there is no bee_init node.

    :param head_tasks: the names of the head tasks
    :type head_tasks: list of strings
    """
    # Return True if more than one head task or if head task is not bee_init
    return not bool(len(head_tasks) == 1 and head_tasks[0] == "bee_init")


def _no_exit_node(tail_tasks):
    """Determine if there is no bee_exit node.

    :param tail_tasks: the names of the tail tasks
    :type tail_tasks: list of strings
    """
    # Return True if more than one tail task or if tail task is not bee_exit
    return not bool(len(tail_tasks) == 1 and tail_tasks[0] == "bee_exit")
