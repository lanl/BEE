"""Defines data structures for holding task and workflow data."""
from collections import namedtuple
from uuid import uuid4

# Workflow input parameter class
InputParameter = namedtuple("InputParameter", ["id", "type", "value"])
# Workflow output parameter class
OutputParameter = namedtuple("OutputParameter", ["id", "source", "type", "value"])
# Step input class
StepInput = namedtuple("StepInput", ["id", "source", "type", "value", "optional", "prefix",
                                     "position"])
# Step output class
StepOutput = namedtuple("StepOutput", ["id", "glob", "type", "value"])

# CWL requirement class
Requirement = namedtuple("Requirement", ["class_", "params"])
# CWL hint class
Hint = namedtuple("Hint", ["class_", "params"])


class Workflow:
    """Data structure for holding data about a workflow."""

    def __init__(self, name, hints, requirements, inputs, outputs, workflow_id=None):
        """Store a workflow description.

        :param name: the workflow name
        :type name: string
        :param hints: the workflow hints
        :type hints: list of Requirements
        :param requirements: the workflow requirements
        :type requirements: list of Requirements
        :param inputs: the workflow inputs
        :type inputs: set of strings
        :param outputs: the workflow outputs
        :type outputs: set of strings
        :param workflow_id: the workflow ID
        :type workflow_id: str
        """
        self.name = name
        self.hints = hints
        self.requirements = requirements
        self.inputs = inputs
        self.outputs = outputs

        # Workflow ID as UUID if not given
        if workflow_id:
            self.id = workflow_id
        else:
            self.id = str(uuid4())

    def __eq__(self, other):
        """Test the equality of two workflows.

        Workflow ID and dependencies do not factor into equality testing.
        Currently, the code is boilerplate. We do not support multiple workflows.

        :param other: the workflow with which to test equality
        :type other: instance of Workflow
        """
        return bool(self.name == other.name and
                    sorted(self.hints) == sorted(other.hints) and
                    sorted(self.requirements) == sorted(other.requirements) and
                    self.inputs == other.inputs and
                    self.outputs == other.outputs)

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: instance of Workflow
        """
        return bool(not self.__eq__(other))

    def __repr__(self):
        """Construct a workflow's string representation."""
        return (f"<Workflow id={self.id} name='{self.name}' hints={self.hints} "
                f"requirements = {self.requirements} inputs={self.inputs} outputs={self.outputs}>")


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, command, hints, requirements, subworkflow, inputs, outputs,
                 workflow_id, task_id=None):
        """Store a task description.

        Task ID should only be given as a parameter when reconstructing the Task object
        from the graph database.

        :param name: the task name
        :type name: str
        :param command: the command to run for the task
        :type command: list of str
        :param hints: the task hints (optional requirements)
        :type hints: list of Hint
        :param requirements: the task requirements
        :type requirements: list of Requirement
        :param subworkflow: an identifier for the subworkflow to which the task belongs
        :type subworkflow: str
        :param inputs: the task inputs
        :type inputs: set of str
        :param outputs: the task outputs
        :type outputs: set of str
        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param task_id: the task ID
        :type task_id: str
        """
        self.name = name
        self.command = command
        self.hints = hints
        self.requirements = requirements
        self.subworkflow = subworkflow
        self.inputs = inputs
        self.outputs = outputs
        self.workflow_id = workflow_id

        # Task ID as UUID if not given
        if task_id:
            self.id = task_id
        else:
            self.id = str(uuid4())

    def __eq__(self, other):
        """Test the equality of two tasks.

        Task ID and dependencies do not factor into equality testing.
        :param other: the task with which to test equality
        :type other: instance of Task
        """
        return bool(self.name == other.name and
                    self.command == other.command and
                    sorted(self.hints) == sorted(other.hints) and
                    sorted(self.requirements) == sorted(other.requirements) and
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
                f"requirements = {self.requirements} subworkflow='{self.subworkflow}' "
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

