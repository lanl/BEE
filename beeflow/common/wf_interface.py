"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface.
"""

from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
from beeflow.common.data.wf_data import Task, Workflow

GraphDatabaseInterface.connect(password="password")


def create_task(name, base_command, arguments=None, dependencies=None, subworkflow=""):
    """Create a new BEE workflow task.

    :param name: the name given to the task
    :type name: string
    :param base_command: the base command for the task
    :type base_command: string
    :param arguments: the arguments given to the task command
    :type arguments: list of strings, or None
    :param dependencies: the task dependencies (on other Tasks)
    :type dependencies: set of task IDs, or None
    :param subworkflow: an identifier for the subworkflow to which the task belongs
    :type subworkflow: string
    """
    if arguments is None:
        arguments = []
    if dependencies is None:
        dependencies = set()

    return Task(name, base_command, arguments, dependencies, subworkflow)


def create_workflow(tasks, outputs=None):
    """Create a new workflow.

    :param tasks: the workflow tasks
    :type tasks: iterable of Task instances
    :param outputs: the workflow outputs
    :type outputs: TBD or None
    """
    new_workflow = Workflow(tasks, outputs)
    GraphDatabaseInterface.load_workflow(new_workflow)
    return new_workflow


def get_subworkflow(subworkflow_id):
    """Get sub-workflows with the specified head tasks.

    :param subworkflow_id: the unique identifier of the subworkflow
    :type subworkflow_id: string
    :rtype: instance of Workflow
    """
    return GraphDatabaseInterface.get_subworkflow(subworkflow_id)


def initialize_workflow():
    """Initialize a BEE workflow."""
    GraphDatabaseInterface.initialize_workflow()


def run_workflow():
    """Run the created workflow."""


def get_dependent_tasks(task):
    """Get the dependents of a task in the BEE workflow.

    :param task: the task whose dependents to obtain
    :type task: instance of Task
    :rtype: set of Task instances
    """
    return GraphDatabaseInterface.get_dependent_tasks(task)


def get_task_state(task):
    """Get the state of the task in the BEE workflow.

    :param task: the task whose state to obtain
    :type task: instance of Task
    :rtype: string
    """
    return GraphDatabaseInterface.get_task_state(task)


def finalize_workflow():
    """Finalize the BEE workflow."""
    GraphDatabaseInterface.finalize_workflow()
