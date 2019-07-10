"""Defines data structures for holding task and workflow data."""


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, base_command, arguments, dependencies, requirements):
        """Store a task description.

        :param task_id: the task ID
        :type task_id: string
        :param name: the task name
        :type name: string
        :param base_command: the base command for the task
        :type base_command: string
        :param arguments: the arguments given to the task
        :type arguments: list of strings
        :param dependencies: the task dependencies (on other tasks)
        :type dependencies: set of Task IDs
        :param requirements: the task requirements
        :type requirements: TBD or None
        """
        self.id = None
        self.name = name
        self.base_command = base_command
        self.arguments = arguments
        self.dependencies = dependencies
        self.requirements = requirements

    def __repr__(self):
        """Construct a task's string representation."""
        return (f"<Task id={self.id} name={self.name} base_command={self.base_command} "
                f"arguments={self.arguments} dependencies={self.dependencies} "
                f"requirements={self.requirements}")

    def construct_command(self):
        """Construct a task's command representation."""
        return (self.base_command if not self.arguments
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
        self.head_tasks = {task for task in tasks if not task.dependencies}

    def __repr__(self):
        """Construct a workflow's string representation."""
        return ("Tasks: " + repr(self.tasks) + "\n"
                + "Outputs: " + repr(self.outputs))
