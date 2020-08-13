"""Defines data structures for holding task and workflow data."""
from collections import namedtuple
import uuid


# Requirement class for storing requirement class, key, and value
Requirement = namedtuple("Requirement", ["req_class", "key", "value"])


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, command, hints, subworkflow, inputs, outputs):
        """Store a task description.

        There are two special tasks: those with the name bee_init and bee_exit.

        bee_init should have no dependencies and all head tasks of the user's
        workflow should depend on it.

        bee_exit should have no dependents and depend on all of the end tasks
        in the user's workflow.

        :param task_id: the task's unique ID (random UUID)
        :type task_id: string
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
        self.id = str(uuid.uuid4())

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



class Workflow:
    """Data structure for holding data about a workflow."""

    def __init__(self, name):
        """Store a workflow description.

        :param task_id: the workflow's unique ID (random UUID)
        :type task_id: string
        :param name: the workflow name
        :type name: string
        """
        self.name = name
        self.id = str(uuid.uuid4())

    def __eq__(self, other):
        """Test the equality of two workflows,

        Workflow ID and dependencies do not factor into equality testing.
        Currently, the code is boilerplate. We do not support multiple workflows.

        :param other: the workflow with which to test equality
        :type other: instance of Workflow
        """
        return bool(self.name == other.name)

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: instance of Worklfow
        """
        return bool(not self.__eq__(other))

    def __hash__(self):
        """Return the hash value for a workflow."""
        return hash(self.name)

    def __repr__(self):
        """Construct a workflow's string representation."""
        return (f"<Workflow id={self.id} name='{self.name}'>")
