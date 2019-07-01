"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface."""

from beeflow.common.gdb.bee_gdb import GraphDatabaseInterface
from beeflow.common.data import Task, Workflow

_gdb_interface = GraphDatabaseInterface()


def create_task(task_id, base_command, arguments=[], dependencies={},
                requirements=None):
    """Create a new BEE workflow task.

    :param task_id: the task ID
    :type task_id: integer
    :param base_command: the base command for the task
    :type base_command: string
    :param arguments: the arguments given to the task
    :type arguments: list of strings
    :param dependencies: the task dependencies (on other Tasks)
    :type dependencies: set of Task instances
    :param requirements: the task requirements
    :type requirements: TBD or None
    """
    return Task(task_id, base_command, arguments, dependencies,
                requirements)


def create_workflow(tasks, outputs=None):
    """Create a new workflow.

    :param tasks: the workflow tasks
    :type tasks: set of Task instances
    :param outputs: the workflow outputs
    :type outputs: TBD or None
    """
    new_workflow = Workflow(tasks, outputs)
    _gdb_interface.load_workflow(new_workflow)


def initialize_workflow():
    """Initialize a BEE workflow."""
    _gdb_interface.initialize_workflow()


def get_dependent_tasks(task):
    """Get the dependents of a task in the BEE workflow.

    :param task: the task whose dependents to obtain
    :type task: instance of Task
    :rtype: set of Task instances
    """
    return _gdb_interface.get_dependent_tasks(task)


def get_subworkflow(tasks):
    """Get sub-workflows with the specified head tasks.

    :param tasks: the head tasks of the sub-workflows
    :type tasks: set of Task instances
    :rtype: instance of Workflow
    """


def finalize_workflow():
    """Finalize the BEE workflow."""
    _gdb_interface.finalize_workflow()
