"""Defines data structures for holding task and workflow data."""


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, task_id, name, commands, requirements, hints, subworkflow, inputs, outputs):
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
        :param commands: the command(s) for the task
        :type commands: list of lists of strings
        :param requirements: the task requirements
        :type requirements: dictionary
        :param hints: the task hints (optional requirements)
        :type hints: dictionary
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string
        :param inputs: the task inputs
        :type inputs: set
        :param outputs: the task outputs
        :type outputs: set
        """
        self.id = task_id
        self.name = name
        self.commands = commands
        self.requirements = requirements
        self.hints = hints
        self.subworkflow = subworkflow
        self.inputs = inputs
        self.outputs = outputs

        self.dependencies = None

    def __eq__(self, other):
        """Test the equality of two tasks.

        :param other: the task with which to test equality
        :type other: instance of Task
        """
        return bool(self.id == other.id and
                    self.name == other.name and
                    self.commands == other.commands and
                    self.requirements == other.requirements and
                    self.hints == other.hints and
                    self.subworkflow == other.subworkflow and
                    self.inputs == other.inputs and
                    self.outputs == other.outputs and
                    self.dependencies == other.dependencies)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: instance of Task
        """
        return not self.__eq__(other)

    def __hash__(self):
        """Return the hash value for a task."""
        return hash((self.id, self.name))

    def __repr__(self):
        """Construct a task's string representation."""
        return f"<Task id={self.id} name={self.name}>"

    def construct_commands(self):
        """Construct a task's command representation."""
        return [" ".join(command) for command in self.commands]

    @property
    def base_commands(self):
        """Return a list of the task base commands.

        :rtype: list of strings
        """
        return [command[0] for command in self.commands]


class Workflow:
    """Data structure for holding workflow data and metadata."""

    def __init__(self, tasks, requirements, hints):
        """Initialize a new workflow data structure.

        :param tasks: the workflow tasks
        :type tasks: iterable of Task instances
        :param requirements: the workflow requirements
        :type requirements: dictionary
        :param hints: the workflow hints (optional requirements)
        :type hints: dictionary
        """
        self._tasks = {task.id: task for task in tasks}
        self.requirements = requirements
        self.hints = hints

    def __eq__(self, other):
        """Test the equality of two workflows.

        :param other: the workflow with which to test equality
        :type other: instance of Workflow
        :rtype: boolean
        """
        return bool(self.tasks == other.tasks and
                    self.requirements == other.requirements and
                    self.hints == other.hints)

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
                + "Hints: " + repr(self.hints))

    @property
    def tasks(self):
        """Return the workflow tasks as a set."""
        return set(self._tasks.values())
