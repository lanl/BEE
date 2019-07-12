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


def get_subworkflow(subworkflow):
    """Get sub-workflows from the graph database with the specified head tasks.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: instance of Workflow
    """
    return _GDB_DRIVER.get_subworkflow(subworkflow)


def initialize_workflow():
    """Start the workflow loaded into the graph database."""
    _GDB_DRIVER.initialize_workflow()


def get_dependent_tasks(task):
    """Get the dependents of a task in a graph database workflow.

    :param task: the task whose dependents to obtain
    :type task: instance of Task
    :rtype: set of Task instances
    """
    return _GDB_DRIVER.get_dependent_tasks(task)


def get_task_state(task):
    """Get the state of a task in a graph database workflow.

    :param task: the task whose state to obtain
    :type task: instance of Task
    :rtype: string
    """
    return _GDB_DRIVER.get_task_state(task)


def finalize_workflow():
    """Finalize the BEE workflow loaded into the graph database."""
    _GDB_DRIVER.finalize_workflow()
