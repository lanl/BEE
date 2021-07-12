"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface instance.
"""

from uuid import uuid4
from beeflow.common.gdb_interface import GraphDatabaseInterface
from beeflow.common.wf_data import Workflow, Task, Requirement, Hint


class WorkflowInterface:
    """Interface for manipulating workflows."""

    def __init__(self, **kwargs):
        """Initialize the Workflow interface.

        Initializing this interface automatically attempts to
        connect to the graph database.

        :param kwargs: arguments to be passed to the graph database
        """
        self._gdb_interface = GraphDatabaseInterface()
        # In the future we may need to grab the details from a config file
        self._gdb_details = kwargs
        # Store the Workflow ID in the interface to assign it to new task objects
        self._workflow_id = None

    def initialize_workflow(self, name, inputs, outputs, requirements=None, hints=None):
        """Begin construction of a BEE workflow.

        :param name: the workflow name
        :type name: str
        :param inputs: the inputs to the workflow
        :type inputs: set of str
        :param outputs: the outputs of the workflow
        :type outputs: set of str
        :param requirements: the workflow requirements
        :type requirements: list of Requirement
        :param hints: the workflow hints (optional requirements)
        :type hints: list of Hint
        """
        if requirements is None:
            requirements = set()
        if hints is None:
            hints = set()

        # Connect to the graph database
        self._gdb_interface.connect(**self._gdb_details)

        workflow = Workflow(name, hints, requirements, inputs, outputs)
        self._workflow_id = workflow.id

        # Load the new workflow into the graph database
        self._gdb_interface.initialize_workflow(workflow)

        return workflow

    def execute_workflow(self):
        """Begin execution of a BEE workflow."""
        self._gdb_interface.execute_workflow()

    def pause_workflow(self):
        """Pause the execution of a BEE workflow."""
        self._gdb_interface.pause_workflow()

    def resume_workflow(self):
        """Resume the execution of a paused BEE workflow."""
        self._gdb_interface.resume_workflow()

    def reset_workflow(self):
        """Reset the execution state and ID of a BEE workflow."""
        self._gdb_interface.reset_workflow(str(uuid4()))

    def finalize_workflow(self):
        """Deconstruct a BEE workflow."""
        self._gdb_interface.cleanup()

    @staticmethod
    def create_requirement(class_, params):
        """Create a workflow requirement.

        :param class_: the requirement class
        :type class_: str
        :param params: the requirement parameters (key-value pairs)
        :type params: dict
        :rtype: Requirement
        """
        return Requirement(class_, params)

    @staticmethod
    def create_hint(class_, params):
        """Create a workflow hint.

        :param class_: the requirement class
        :type class_: str
        :param params: the requirement parameters (key-value pairs)
        :type params: dict
        :rtype: Hint
        """
        return Hint(class_, params)

    def add_task(self, name, command=None, requirements=None, hints=None, subworkflow=None,
                 inputs=None, outputs=None):
        """Add a new task to a BEE workflow.

        :param name: the name given to the task
        :type name: str
        :param command: the command for the task
        :type command: list of str
        :param requirements: the task-specific requirements
        :type requirements: list of Requirement
        :param hints: the task-specific hints (optional requirements)
        :type hints: list of Hint
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: str
        :param inputs: the task inputs
        :type inputs: set of str
        :param outputs: the task outputs
        :type outputs: set of str
        :rtype: Task
        """
        # Immutable default arguments
        if command is None:
            command = []
        if requirements is None:
            requirements = set()
        if hints is None:
            hints = set()
        if inputs is None:
            inputs = set()
        if outputs is None:
            outputs = set()

        task = Task(name, command, hints, requirements, subworkflow, inputs, outputs,
                    self._workflow_id)
        # Load the new task into the graph database
        self._gdb_interface.load_task(task)
        return task

    def initialize_ready_tasks(self):
        """Initialize runnable tasks in a BEE workflow to ready."""
        self._gdb_interface.initialize_ready_tasks()

    def finalize_task(self, task):
        """Mark a BEE workflow task as completed.

        This method also automatically deduces what tasks are now
        runnable, updating their states to ready and returning a
        set of the runnable tasks.

        :param task: the task to finalize
        :type task: Task
        :rtype: set of Task
        """
        self._gdb_interface.finalize_task(task)
        self._gdb_interface.initialize_ready_tasks()
        return self._gdb_interface.get_ready_tasks()

    def get_task_by_id(self, task_id):
        """Get a task by its Task ID.

        :param task_id: the task's ID
        :type task_id: str
        :rtype: Task
        """
        return self._gdb_interface.get_task_by_id(task_id)

    def get_workflow(self):
        """Get a loaded BEE workflow.

        Returns a tuple of (workflow_description, tasks)

        :rtype: tuple of (Workflow, set of Task)
        """
        workflow = self._gdb_interface.get_workflow_description()
        tasks = self._gdb_interface.get_workflow_tasks()
        return workflow, tasks

    def get_subworkflow(self, subworkflow):
        """Get a subworkflow by its identifier.

        Returns a tuple of (tasks, requirements, hints).

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: str
        :rtype: tuple of (set of Task, set of Requirement, set of Hint)
        """
        subworkflow_tasks = self._gdb_interface.get_subworkflow_tasks(subworkflow)
        requirements, hints = self._gdb_interface.get_workflow_requirements_and_hints()
        return subworkflow_tasks, requirements, hints

    def get_ready_tasks(self):
        """Get ready tasks from a BEE workflow.

        :rtype: set of Task
        """
        return self._gdb_interface.get_ready_tasks()

    def get_dependent_tasks(self, task):
        """Get the dependents of a task in a BEE workflow.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: set of Task
        """
        return self._gdb_interface.get_dependent_tasks(task)

    def get_task_state(self, task):
        """Get the state of the task in a BEE workflow.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._gdb_interface.get_task_state(task)

    def set_task_state(self, task, state):
        """Set the state of the task in a BEE workflow.

        This method should not be used to set a task as completed.
        finalize_task() should instead be used.

        :param task: the task whose state to set
        :type task: Task
        :param state: the new state of the task
        :type state: str
        """
        self._gdb_interface.set_task_state(task, state)

    def get_task_metadata(self, task, keys):
        """Get the job description metadata of a task in a BEE workflow.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :param keys: the metadata keys whose values to retrieve
        :type keys: iterable of str
        :rtype: dict
        """
        return self._gdb_interface.get_task_metadata(task, keys)

    def set_task_metadata(self, task, metadata):
        """Set the job description metadata of a task in a BEE workflow.

        This method should not be used to update task state.
        finalize_task() should instead be used.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._gdb_interface.set_task_metadata(task, metadata)

    def workflow_completed(self):
        """Return true if all of a workflow's tasks have completed, else false.

        :rtype: bool
        """
        return self._gdb_interface.workflow_completed()

    def workflow_initialized(self):
        """Return true if a workflow has been initialized, else false.

        Currently functionally the same as workflow_loaded() but may
        change when multiple workflows per database instance are supported.

        :rtype: bool
        """
        return self._gdb_interface.initialized()

    def workflow_loaded(self):
        """Return true if a workflow is loaded, else false.

        :rtype: bool
        """
        return bool(not self._gdb_interface.empty())
