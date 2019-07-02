"""Defines data structures for holding task and workflow data."""


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, task_id, base_command, arguments, dependencies,
                 requirements):
        """Store a task description.

        :param task_id: the name given to the task
        :type task_id: integer
        :param base_command: the base command for the task
        :type base_command: string
        :param arguments: the arguments given to the task
        :type arguments: list of strings or None
        :param dependencies: the task dependencies (on other Tasks)
        :type dependencies: set of Task objects or None
        :param requirements: the task requirements
        :type requirements: TBD or None
        """
        self.id = task_id
        self.base_command = base_command
        self.arguments = arguments
        self.dependencies = dependencies
        self.requirements = requirements

    def __repr__(self):
        """Construct a task's command representation."""
        return self.construct_command()

    def construct_command(self):
        """Construct a task's command representation."""
        return (self.base_command if self.arguments is None
                else " ".join([self.base_command] + self.arguments))


class Workflow:
    """Data structure for holding workflow data and metadata."""

    def __init__(self, tasks, outputs):
        """Initialize a new workflow data structure.

        :param tasks: the workflow tasks
        :type tasks: set of Task instances
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self.tasks = tasks
        self.outputs = outputs
