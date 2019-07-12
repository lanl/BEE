"""High-level BEE workflow management interface.

Delegates its work to gdb_interface.
"""

import beeflow.common.gdb.gdb_interface as gdb_interface
from beeflow.common.data.wf_data import Task, Workflow

gdb_interface.connect(password="password")

_WORKFLOW = None


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
    :rtype: instance of Task
    """
    if arguments is None:
        arguments = []
    if dependencies is None:
        dependencies = set()

    if not hasattr(create_task, "task_id"):
        create_task.task_id = 0
    else:
        create_task.task_id += 1

    return Task(create_task.task_id, name, base_command, arguments, dependencies, subworkflow)


def create_workflow(tasks, requirements=None, outputs=None):
    """Create a new workflow.

    :param tasks: the workflow tasks
    :type tasks: iterable of Task instances
    :param outputs: the workflow outputs
    :type outputs: TBD or None
    :rtype: instance of Workflow
    """
    return Workflow(tasks, requirements, outputs)


def load_workflow(workflow):
    """Load a workflow.

    :param workflow: the workflow to load
    :type workflow: instance of Workflow
    """
    global _WORKFLOW
    _WORKFLOW = workflow

    gdb_interface.load_workflow(workflow)


def get_subworkflow(subworkflow):
    """Get sub-workflows with the specified head tasks.

    :param subworkflow: the unique identifier of the subworkflow
    :type subworkflow: string
    :rtype: instance of Workflow
    """
    subworkflow_task_ids = gdb_interface.get_subworkflow(subworkflow)
    return create_workflow([_WORKFLOW[task_id] for task_id in subworkflow_task_ids],
                           _WORKFLOW.requirements, _WORKFLOW.outputs)


def initialize_workflow():
    """Initialize a BEE workflow."""
    gdb_interface.initialize_workflow()


def run_workflow():
    """Run the created workflow."""


def get_dependent_tasks(task):
    """Get the dependents of a task in the BEE workflow.

    :param task: the task whose dependents to obtain
    :type task: instance of Task
    :rtype: set of Task instances
    """
    dependent_task_ids = gdb_interface.get_dependent_tasks(task)
    return {_WORKFLOW[task_id] for task_id in dependent_task_ids}


def get_task_state(task):
    """Get the state of the task in the BEE workflow.

    :param task: the task whose state to obtain
    :type task: instance of Task
    :rtype: string
    """
    return gdb_interface.get_task_state(task)


def finalize_workflow():
    """Finalize the BEE workflow."""
    gdb_interface.finalize_workflow()
