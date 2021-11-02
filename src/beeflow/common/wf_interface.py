"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface instance.
"""

from uuid import uuid4
from beeflow.common.gdb_interface import GraphDatabaseInterface
from beeflow.common.wf_data import Workflow, Task


class WorkflowInterface:
    """Interface for manipulating workflows."""

    def __init__(self, **kwargs):
        """Initialize the Workflow interface.

        Initializing this interface automatically attempts to
        connect to the graph database.

        :param kwargs: arguments to be passed to the graph database
        """
        self._gdb_interface = GraphDatabaseInterface()
        # Connect to the graph database
        # In the future, we may want to grab args from a config file
        self._gdb_interface.connect(**kwargs)
        # Store the Workflow ID in the interface to assign it to new task objects
        self._workflow_id = None

    def initialize_workflow(self, name, inputs, outputs, requirements=None, hints=None):
        """Begin construction of a BEE workflow.

        :param name: the workflow name
        :type name: str
        :param inputs: the inputs to the workflow
        :type inputs: list of InputParameter
        :param outputs: the outputs of the workflow
        :type outputs: list of OutputParameter
        :param requirements: the workflow requirements
        :type requirements: list of Requirement
        :param hints: the workflow hints (optional requirements)
        :type hints: list of Hint
        """
        if self.workflow_loaded():
            raise RuntimeError("attempt to re-initialize existing workflow")
        if requirements is None:
            requirements = []
        if hints is None:
            hints = []

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
        self._workflow_id = str(uuid4())
        self._gdb_interface.reset_workflow(self._workflow_id)

    def finalize_workflow(self):
        """Deconstruct a BEE workflow."""
        self._workflow_id = None
        self._gdb_interface.cleanup()

    def add_task(self, name, base_command, inputs, outputs, requirements=None, hints=None,
                 stdout=None):
        """Add a new task to a BEE workflow.

        :param name: the name given to the task
        :type name: str
        :param base_command: the base command for the task
        :type base_command: str or list of str
        :param requirements: the task-specific requirements
        :type requirements: list of Requirement
        :param hints: the task-specific hints (optional requirements)
        :type hints: list of Hint
        :param inputs: the task inputs
        :type inputs: list of StepInput
        :param outputs: the task outputs
        :type outputs: list of StepOutput
        :param stdout: the name of the file to which to redirect stdout
        :type stdout: str
        :rtype: Task
        """
        # Immutable default arguments
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        if requirements is None:
            requirements = []
        if hints is None:
            hints = []

        task = Task(name, base_command, hints, requirements, inputs, outputs, stdout,
                    self._workflow_id)
        # Load the new task into the graph database
        self._gdb_interface.load_task(task)
        return task

    def finalize_task(self, task):
        """Mark a BEE workflow task as completed.

        This method also automatically deduces what tasks are now
        runnable, updating their states to ready and returning a
        list of the runnable tasks.

        :param task: the task to finalize
        :type task: Task
        :rtype: list of Task
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

        :rtype: tuple of (Workflow, list of Task)
        """
        workflow = self._gdb_interface.get_workflow_description()
        tasks = self._gdb_interface.get_workflow_tasks()
        return workflow, tasks

    def get_workflow_outputs(self):
        """Get the outputs from a BEE workflow.

        :rtype: list of OutputParameter
        """
        workflow = self._gdb_interface.get_workflow_description()
        return workflow.outputs

    def get_ready_tasks(self):
        """Get ready tasks from a BEE workflow.

        :rtype: list of Task
        """
        return self._gdb_interface.get_ready_tasks()

    def get_dependent_tasks(self, task):
        """Get the dependents of a task in a BEE workflow.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: list of Task
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
        set_task_state() or finalize_task() should instead be used.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._gdb_interface.set_task_metadata(task, metadata)

    def get_task_input(self, task, input_id):
        """Get a task input object.

        :param task: the task whose input to retrieve
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :rtype: StepInput
        """
        return self._gdb_interface.get_task_input(task, input_id)

    def set_task_input(self, task, input_id, value):
        """Set the value of a task input.

        :param task: the task whose input to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param value: str or int or float
        """
        self._gdb_interface.set_task_input(task, input_id, value)

    def get_task_output(self, task, output_id):
        """Get a task output object.

        :param task: the task whose output to retrieve
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :rtype: StepOutput
        """
        return self._gdb_interface.get_task_output(task, output_id)

    def set_task_output(self, task, output_id, value):
        """Set the value of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param value: the output value to set
        :type value: str or int or float
        """
        self._gdb_interface.set_task_output(task, output_id, value)

    def evaluate_expression(self, task, id, output=False):
        """Evaluate a task input/output expression.

        Expression can be either a string concatenation in a StepInput
        valueFrom field or a parameter substitution in a StepOutput
        glob field. The only special variable supported in valueFrom is
        self.path.

        :param task: the task whose expression to evaluate
        :type task: Task
        :param id: the id of the step input/output
        :type id: str
        :param output: true if output glob expression being evaluated, else false
        :type output: bool
        """
        self._gdb_interface.evaluate_expression(task, id, output)

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

    @property
    def workflow_id(self):
        """Retrieve the workflow ID from the workflow interface.

        If workflow ID is not populated, this grabs it from the database.

        If no workflow is loaded, None is returned.
        :rtype: str
        """
        if self._workflow_id is None and self.workflow_loaded():
            workflow = self.get_workflow()
            self._workflow_id = workflow.id

        return self._workflow_id
