"""Defines data structures for holding task and workflow data."""
from collections import namedtuple
import time

# Requirement class for storing requirement class, key, and value
Requirement = namedtuple("Requirement", ["req_class", "key", "value"])
Hint = namedtuple("Hint", ["req_class", "key", "value"])


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, command, hints, subworkflow, inputs, outputs):
        """Store a task description.

        There are two special tasks: those with the name bee_init and bee_exit.
        bee_init should have no dependencies and all head tasks of the user's
        workflow should depend on it.
        bee_exit should have no dependents and depend on all of the end tasks
        in the user's workflow.
        :param wf_id: the unique id of the workflow that the task belongs to
        :type wf_id: string
        :param task_id: the task's unique ID
        :type task_id: integer
        :param name: the task name
        :type name: string
        :param command: the command to run for the task
        :type command: list of strings
        :param hints: the task hints (optional requirements)
        :type hints: dictionary
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string
        :param inputs: the task inputs
        :type inputs: set
        :param outputs: the task outputs
        :type outputs: set
        """
        self.name = name
        self.command = command
        self.hints = hints
        self.subworkflow = subworkflow
        self.inputs = inputs
        self.outputs = outputs

        # Workflow ID
        self.wf_id = 'workflow_id'
        # Task ID
        self.id = abs(hash(self))

    def __eq__(self, other):
        """Test the equality of two tasks.

        Task ID and dependencies do not factor into equality testing.
        :param other: the task with which to test equality
        :type other: instance of Task
        """
        return bool(self.name == other.name and
                    self.command == other.command and
                    self.hints == other.hints and
                    self.subworkflow == other.subworkflow and
                    self.inputs == other.inputs and
                    self.outputs == other.outputs)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: instance of Task
        """
        return bool(not self.__eq__(other))

    def __hash__(self):
        """Return the hash value for a task."""
        return hash((self.name, self.subworkflow))

    def __repr__(self):
        """Construct a task's string representation."""
        return (f"<Task id={self.id} name='{self.name}' command={self.command} hints={self.hints} "
                f"subworkflow='{self.subworkflow}' inputs={self.inputs} outputs={self.outputs}>")

    def construct_command(self):
        """Construct a task's command representation."""
        return "".join(self.command)

    @property
    def base_command(self):
        """Return a list of the task base command.

        :rtype: list of strings
        """
        return self.command[0]


class BuildTask:
    """Data structure for holding data about a single task."""

    def __init__(self, name, command, subworkflow, inputs, outputs, hints=None, requirements=None):
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
        :param command: the command to run for the task
        :type command: list of strings
        :param hints: the task hints (optional)
        :type hints: dictionary
        :param hints: the task requirements (optional)
        :type hints: dictionary
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: string
        :param inputs: the task inputs
        :type inputs: set
        :param outputs: the task outputs
        :type outputs: set
        """
        self.name = name
        self.command = command
        self.hints = hints
        self.requirements = requirements
        self.subworkflow = subworkflow
        self.inputs = inputs
        self.outputs = outputs

        # Task ID
        self.id = abs(hash(self))

    def __eq__(self, other):
        """Test the equality of two tasks.

        Task ID and dependencies do not factor into equality testing.

        :param other: the task with which to test equality
        :type other: instance of Task
        """
        return bool(self.name == other.name and
                    self.command == other.command and
                    self.hints == other.hints and
                    self.requirements == other.requirements and
                    self.subworkflow == other.subworkflow and
                    self.inputs == other.inputs and
                    self.outputs == other.outputs)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: instance of Task
        """
        return bool(not self.__eq__(other))

    def __hash__(self):
        """Return the hash value for a task."""
        return hash((self.name, time.time()))

    def __repr__(self):
        """Construct a task's string representation."""
        return (f"<Task id={self.id} name='{self.name}' command={self.command} hints={self.hints} "
                f"requirements={self.requirements} subworkflow='{self.subworkflow}'"
                f"inputs={self.inputs} outputs={self.outputs}>")

    def construct_command(self):
        """Construct a task's command representation."""
        return "".join(self.command)

    @property
    def base_command(self):
        """Return a list of the task base command.

        :rtype: list of strings
        """
        return self.command[0]
