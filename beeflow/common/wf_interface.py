"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface.
"""

from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
from beeflow.common.data.wf_data import Task, Workflow

_GDB_INTERFACE = GraphDatabaseInterface(password="password")


def create_task(task_id, name, base_command, arguments=None, dependencies=None, requirements=None):
    """Create a new BEE workflow task.

    :param task_id: the ID given to the task
    :type task_id: string
    :param name: the name given to the task
    :type name: string
    :param base_command: the base command for the task
    :type base_command: string
    :param arguments: the arguments given to the task command
    :type arguments: list of strings, or None
    :param dependencies: the task dependencies (on other Tasks)
    :type dependencies: set of task IDs, or None
    :param requirements: the task requirements
    :type requirements: TBD, or None
    """
    if arguments is None:
        arguments = []
    if dependencies is None:
        dependencies = set()

    return Task(task_id, name, base_command, arguments, dependencies, requirements)


def create_workflow(tasks, outputs=None):
    """Create a new workflow.

    :param tasks: the workflow tasks
    :type tasks: set of Task instances
    :param outputs: the workflow outputs
    :type outputs: TBD or None
    """
    new_workflow = Workflow(tasks, outputs)
    _GDB_INTERFACE.load_workflow(new_workflow)
    return new_workflow


def initialize_workflows():
    """Initialize a BEE workflow."""
    _GDB_INTERFACE.initialize_workflows()


def get_dependent_tasks(task):
    """Get the dependents of a task in the BEE workflow.

    :param task: the task whose dependents to obtain
    :type task: instance of Task
    :rtype: set of Task instances
    """
    return _GDB_INTERFACE.get_dependent_tasks(task)


def get_subworkflow(head_tasks):
    """Get sub-workflows with the specified head tasks.

    :param tasks: the head tasks of the sub-workflows
    :type tasks: set of Task instances
    :rtype: instance of Workflow
    """


def finalize_workflows():
    """Finalize the BEE workflow."""
    _GDB_INTERFACE.finalize_workflows()
