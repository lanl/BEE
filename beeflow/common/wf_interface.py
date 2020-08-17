"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface instance.
"""

from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
from beeflow.common.data.wf_data import Workflow, Task, Requirement


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

    def initialize_workflow(self, name, inputs, outputs, requirements=None, hints=None):
        """Begin construction of a BEE workflow.

        :param name: a name for the workflow
        :type name: string
        :param inputs: the inputs to the workflow
        :type inputs: set of strings
        :param outputs: the outputs of the workflow
        :type outputs: set of strings
        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        """
        if requirements is None:
            requirements = set()
        if hints is None:
            hints = set()

        # Connect to the graph database
        self._gdb_interface.connect(**self._gdb_details)

        # Create workflow object and initialize graph database
        workflow = Workflow(name, hints, requirements, inputs, outputs)
        self._gdb_interface.initialize_workflow(workflow)

    def execute_workflow(self):
        """Begin execution of the BEE workflow."""
        self._gdb_interface.execute_workflow()

    def finalize_workflow(self):
        """Deconstruct the BEE workflow."""
        self._gdb_interface.cleanup()

    @staticmethod
    def create_requirement(req_class, key, value):
        """Create a workflow requirement.

        :param req_class: the requirement class
        :type req_class: string
        :param key: the requirement key
        :type key: string
        :param value: the requirement value
        :type value: string, boolean, or integer
        """
        return Requirement(req_class, key, value)

    def add_task(self, name, command=None, hints=None, requirements=None, subworkflow=None,
                 inputs=None, outputs=None, scatter=False, glob=None):
        """Create a new BEE workflow task.

        In its current form, this method allows the user to create bee_init and bee_exit
        nodes manually.

        :param name: the name given to the task
        :type name: string
        :param command: the command for the task
        :type command: list of strings
        :param hints: the task-specific hints (optional requirements)
        :type hints: set of Requirement instances
        :param requirements: the task-specific requirements
        :type requirements: set of Requirement instances
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string
        :param inputs: the task inputs
        :type inputs: set of strings
        :param outputs: the task outputs
        :type outputs: set of strings
        :param scatter: set to true if the task scatters over its input
        :type scatter: bool
        :param glob: the task output binding
        :type glob: string
        :rtype: instance of Task
        """
        # Immutable default arguments
        if command is None:
            command = []
        if hints is None:
            hints = set()
        if inputs is None:
            inputs = set()
        if outputs is None:
            outputs = set()

        task = Task(name, command, hints, requirements, subworkflow, inputs, outputs, scatter,
                    glob)
        self._gdb_interface.load_task(task)
        return task

    def scatter_task(self, task):
        """Expand a scatter task into unique tasks for each of its input.

        :param task: the task to expand (must have scatter set to true)
        :type task: instance of Task
        """
        _task = self.get_task_by_id(task.id)
        if _task.scatter:
            self._gdb_interface.scatter_task(task)
        else:
            raise ValueError(f"Task {task.name} is not set to scatter")

    def get_task_by_id(self, task_id):
        """Get a task by its Task ID.

        :param task_id: the task's ID
        :type task_id: str
        :rtype: instance of Task
        """
        return self._gdb_interface.get_task_by_id(task_id)

    def get_workflow(self):
        """Get the loaded workflow.

        Returns a tuple of (tasks, requirements, hints).

        :rtype: tuple of (set, set, set)
        """
        # Obtain a list of workflow tasks
        workflow_tasks = self._gdb_interface.get_workflow_tasks()
        # Obtain the workflow requirements, hints
        requirements, hints = self._gdb_interface.get_workflow_requirements_and_hints()
        # Return a new Workflow object with the given tasks (don't reset IDs)
        return (workflow_tasks, requirements, hints)

    def get_subworkflow(self, subworkflow):
        """Get a subworkflow by its identifier.

        Returns a tuple of (tasks, requirements, hints).

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: a tuple of (set, set of Requirement, set of Requirement)
        """
        # Obtain a list of the subworkflow tasks
        subworkflow_tasks = self._gdb_interface.get_subworkflow_tasks(subworkflow)
        # Obtain the subworkflow requirements, hints
        requirements, hints = self._gdb_interface.get_workflow_requirements_and_hints()

        # Return a new Workflow object with the given tasks
        return (subworkflow_tasks, requirements, hints)

    def get_dependent_tasks(self, task):
        """Return the dependents of a task in the BEE workflow.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: set of Task instances
        """
        # Return a set of the dependent Task objects
        return self._gdb_interface.get_dependent_tasks(task)

    def get_task_state(self, task):
        """Return the state of the task in the BEE workflow.

        :param task: the task whose state to retrieve
        :type task: instance of Task
        :rtype: string
        """
        return self._gdb_interface.get_task_state(task)

    def set_task_state(self, task, state):
        """Set the state of a task in the BEE workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        :param state: the new state
        :type state: string
        """
        self._gdb_interface.set_task_state(task, state)

    def set_task_inputs(self, task, inputs):
        """Set the inputs of a task in the BEE workflow.

        Dependencies will automatically be updated.

        :param task: the task to modify
        :type task: instance of Task
        :param inputs: the new inputs
        :type inputs: set of strings
        """
        self._gdb_interface.set_task_inputs(task, inputs)

    def set_task_outputs(self, task, outputs):
        """Set the outputs of a task in the BEE workflow.

        Dependencies will automatically be updated.

        :param task: the task to modify
        :type task: instance of Task
        :param outputs: the new inputs
        :type outputs: set of strings
        """
        self._gdb_interface.set_task_outputs(task, outputs)

    def workflow_initialized(self):
        """Return true if a workflow has been initialized, else false.

        :rtype: boolean
        """
        return self._gdb_interface.initialized()

    def workflow_loaded(self):
        """Return true if a workflow is loaded, else false.

        :rtype: boolean
        """
        return bool(not self._gdb_interface.empty())
