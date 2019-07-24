"""Defines data structures for holding task and workflow data."""


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, task_id, name, base_command, arguments, dependencies, requirements,
                 hints, subworkflow, inputs, outputs):
        """Store a task description.

        There are two special tasks: those with the name bee_init and bee_exit.

        bee_init should have no dependencies and all head tasks of the user's
        workflow should depend on it.

        bee_exit should have no dependents and depend on all of the end tasks
        in the user's workflow.

        :param task_id: the task's unique ID
        :type task_id: integer
        :param name: the task name
        :type name: string
        :param base_command: the base command for the task
        :type base_command: string
        :param arguments: the arguments given to the task
        :type arguments: list of strings
        :param dependencies: the task dependencies (on other tasks)
        :type dependencies: set of Task IDs
        :param requirements: the task requirements
        :type requirements: TBD
        :param hints: the task hints (optional requirements)
        :type hints: TBD
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string
        :param inputs: the task inputs
        :type inputs: TBD
        :param outputs: the task outputs
        :type outputs: TBD
        """
        self.id = task_id
        self.name = name
        self.base_command = base_command
        self.arguments = arguments
        self.dependencies = dependencies
        self.requirements = requirements
        self.hints = hints
        self.subworkflow = subworkflow
        self.inputs = inputs
        self.outputs = outputs

    def __eq__(self, other):
        """Test the equality of two tasks.

        :param other: the task with which to test equality
        :type other: instance of Task
        """
        return bool(self.id == other.id and
                    self.name == other.name and
                    self.base_command == other.base_command and
                    self.arguments == other.arguments and
                    self.dependencies == other.dependencies and
                    self.requirements == other.requirements and
                    self.hints == other.hints and
                    self.subworkflow == other.subworkflow and
                    self.inputs == other.inputs and
                    self.outputs == other.outputs)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: instance of Task
        """
        return not self.__eq__(other)

    def __hash__(self):
        """Return the hash value for a task."""
        return hash((self.id, self.name, self.base_command, self.subworkflow))

    def __repr__(self):
        """Construct a task's string representation."""
        return (f"<Task id={self.id} name={self.name} base_command={self.base_command} "
                f"arguments={self.arguments} dependencies={self.dependencies}")

    def construct_command(self):
        """Construct a task's command representation."""
        return (self.base_command if not self.arguments
                else " ".join([self.base_command] + self.arguments))


class Workflow:
    """Data structure for holding workflow data and metadata."""

    def __init__(self, tasks, requirements, hints, inputs, outputs):
        """Initialize a new workflow data structure.

        :param tasks: the workflow tasks
        :type tasks: iterable of Task instances
        :param requirements: the workflow requirements
        :type requirements: TBD
        :param hints: the workflow hints (optional requirements)
        :type hints: TBD
        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self._tasks = {task.id: task for task in tasks}
        self.requirements = requirements
        self.hints = hints
        self.inputs = inputs
        self.outputs = outputs

    def __eq__(self, other):
        """Test the equality of two workflows.

        :param other: the workflow with which to test equality
        :type other: instance of Workflow
        :rtype: boolean
        """
        return bool(self.tasks == other.tasks and
                    self.requirements == other.requirements and
                    self.hints == other.hints and
                    self.outputs == other.outputs)

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: instance of Workflow
        :rtype: boolean
        """
        return not self.__eq__(other)

    def __getitem__(self, task_id):
        """Retrieve a Task instance by its ID, if it exists.

        :param task_id: the ID of the task to retrieve
        :type task: integer
        :rtype: instance of Task
        """
        return self._tasks.get(task_id, None)

    def __contains__(self, task):
        """Check if a task is in the workflow.

        :param task: the task to check for
        :type task: instance of Task
        :rtype: boolean
        """
        return bool(task.id in self._tasks and self._tasks[task.id] == task)

    def __repr__(self):
        """Construct a workflow's string representation.

        :rtype: string
        """
        return ("Tasks: " + repr(self.tasks) + "\n"
                + "Requirements: " + repr(self.requirements) + "\n"
                + "Outputs: " + repr(self.outputs))

    @property
    def tasks(self):
        """Return the workflow tasks as a set."""
        return set(self._tasks.values())
