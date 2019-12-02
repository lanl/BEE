"""High-level BEE workflow management interface.

Delegates its work to a GDBInterface instance.
"""

from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
from beeflow.common.data.wf_data import Task, Workflow, Requirement


class WorkflowInterface:
    """Interface for manipulating workflows."""

    def __init__(self, **kwargs):
        """Initialize the Workflow interface.

        Initializing this interface automatically attempts to
        connect to the graph database.

        :param kwargs: arguments to be passed to the graph database
        """
        # In the future we may need to grab the details from a config file
        self._gdb_interface = GraphDatabaseInterface()
        self._gdb_interface.connect(**kwargs)

    @staticmethod
    def create_task(name, command=None, hints=None, subworkflow=None, inputs=None, outputs=None):
        """Create a new BEE workflow task.

        In its current form, this method allows the user to create bee_init and bee_exit
        nodes manually.

        :param name: the name given to the task
        :type name: string
        :param command: the command for the task
        :type command: list of strings
        :param hints: the task-specific hints (optional requirements)
        :type hints: set of Requirement instances, or None
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string or None
        :param inputs: the task inputs
        :type inputs: set of strings, or None
        :param outputs: the task outputs
        :type outputs: set of strings, or None
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

        # Standard bee_init, bee_exit tasks
        if name.lower() == "bee_init":
            name = name.lower()
        elif name.lower() == "bee_exit":
            name = name.lower()

        return Task(name, command, hints, subworkflow, inputs, outputs)

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

    @staticmethod
    def create_workflow(tasks, requirements=None, hints=None, assign_ids=True):
        """Create a new workflow.

        :param tasks: the workflow tasks
        :type tasks: list of Task instances
        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances, or None
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances, or None
        :param assign_ids: some reconstructions do not require IDs
        :type assign_ids: boolean
        :rtype: instance of Workflow
        """
        if requirements is None:
            # Immutable default argument
            requirements = set()
        if hints is None:
            # Immutable default argument
            hints = set()

        def _resolve_head_tasks(tasks):
            """Return all head tasks in a list of tasks.

            :param tasks: the tasks to parse
            :type tasks: list of Task instances
            :rtype: list of Task instances
            """
            # Head tasks are those that do not depend on any other tasks' outputs
            return [task for task in tasks if all(task.inputs.isdisjoint(other.outputs)
                                                  for other in tasks if other != task)]

        def _resolve_tail_tasks(tasks):
            """Return all tail tasks in a list of tasks.

            :param tasks: the tasks to parse
            :type tasks: list of Task instances
            :rtype: list of Task instances
            """
            # Tail tasks are those for which no other tasks depend on their outputs
            return [task for task in tasks if all(task.outputs.isdisjoint(other.inputs)
                                                  for other in tasks if other != task)]

        # Create bee_init if it doesn't exist
        if not any(task.name == "bee_init" for task in tasks):
            # Get a list of head tasks
            head_tasks = _resolve_head_tasks(tasks)
            # Form the union of their inputs
            inputs = set().union(*(head_task.inputs for head_task in head_tasks))
            # Create bee_init with inputs and outputs
            tasks.append(WorkflowInterface.create_task("bee_init", inputs=inputs,
                                                       outputs=inputs))

        # Create bee_exit if it doesn't exist
        if not any(task.name == "bee_exit" for task in tasks):
            # Get a list of tail tasks
            tail_tasks = _resolve_tail_tasks(tasks)
            # Form the union of their outputs
            outputs = set().union(*(tail_task.outputs for tail_task in tail_tasks))
            # Create bee_exit with inputs and outputs
            tasks.append(WorkflowInterface.create_task("bee_exit", inputs=outputs,
                                                       outputs=outputs))

        # Assign a task ID to each task (unless we've just yanked the workflow out of the databse)
        if assign_ids:
            for task_id, task in enumerate(tasks):
                task.id = task_id

        # Add task dependencies
        for task in tasks:
            task.dependencies = {other.id for other in tasks if other.id != task.id and not
                                 task.inputs.isdisjoint(other.outputs)}

        return Workflow(tasks, requirements, hints)

    def load_workflow(self, workflow):
        """Load a workflow.

        :param workflow: the workflow to load
        :type workflow: instance of Workflow
        """
        # Store the workflow in the graph database
        self._gdb_interface.load_workflow(workflow)

    def unload_workflow(self):
        """Unload a workflow."""
        # Clean up all data in the database
        self._gdb_interface.cleanup()

    def initialize_workflow(self):
        """Initialize a BEE workflow."""
        self._gdb_interface.initialize_workflow()

    def finalize_workflow(self):
        """Finalize the BEE workflow."""
        self._gdb_interface.finalize_workflow()

    def get_workflow(self):
        """Get the loaded workflow.

        :param requirements: the workflow requirements
        :type requirements: dictionary
        :param hints: the workflow hints (optional requirements)
        :type hints: dictionary
        :rtype: instance of Workflow
        """
        # Obtain a list of workflow tasks
        workflow_tasks = self._gdb_interface.get_workflow_tasks()
        # Obtain the workflow requirements, hints
        requirements, hints = self._gdb_interface.get_workflow_requirements_and_hints()
        # Return a new Workflow object with the given tasks (don't reset IDs)
        return self.create_workflow(workflow_tasks, requirements, hints, False)

    def get_subworkflow(self, subworkflow):
        """Get a subworkflow by its identifier.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: instance of Workflow
        """
        # Obtain a list of the subworkflow tasks
        subworkflow_tasks = self._gdb_interface.get_subworkflow_tasks(subworkflow)
        # Obtain the subworkflow requirements, hints
        requirements, hints = self._gdb_interface.get_workflow_requirements_and_hints()

        # Return a new Workflow object with the given tasks
        return self.create_workflow(subworkflow_tasks, requirements, hints)

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
        """Set the state of the task in the BEE workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        :param state: the new state
        :type state: string
        """
        return self._gdb_interface.set_task_state(task)

    def workflow_loaded(self):
        """Return true if a workflow is loaded, else false.

        :rtype: boolean
        """
        return bool(not self._gdb_interface.empty())
