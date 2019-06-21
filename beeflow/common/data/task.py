"""Defines a data structure for holding task data."""


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, task_id, base_command, arguments=None,
                 dependencies=None, requirements=None):
        """Store a task description.

        :param name (str): The name given to the task
        :param command (str): The base command for the task
        :param arguments (list): The arguments given to the task
        :param requirements (list): The command requirements (dependencies)
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
                else self.base_command + " " + " ".join(self.arguments))
