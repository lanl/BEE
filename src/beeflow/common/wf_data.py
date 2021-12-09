"""Defines data structures for holding task and workflow data."""
from collections import namedtuple
from uuid import uuid4

# Workflow input parameter class
InputParameter = namedtuple("InputParameter", ["id", "type", "value"])
# Workflow output parameter class
OutputParameter = namedtuple("OutputParameter", ["id", "type", "value", "source"])
# Step input class
StepInput = namedtuple("StepInput", ["id", "type", "value", "default", "source", "prefix",
                                     "position", "value_from"])
# Step output class
StepOutput = namedtuple("StepOutput", ["id", "type", "value", "glob"])

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
        :type inputs: list of InputParameter
        :param outputs: the workflow outputs
        :type outputs: list of OutputParameter
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
        id_sort = lambda i: i.id
        return bool(self.name == other.name and
                    sorted(self.hints) == sorted(other.hints) and
                    sorted(self.requirements) == sorted(other.requirements) and
                    sorted(self.inputs, key=id_sort) == sorted(other.inputs, key=id_sort) and
                    sorted(self.outputs, key=id_sort) == sorted(other.outputs, key=id_sort))

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: instance of Workflow
        """
        return bool(not self.__eq__(other))

    def __repr__(self):
        """Construct a workflow's string representation."""
        return (f"<Workflow id={self.id} name={self.name} hints={self.hints} "
                f"requirements = {self.requirements} inputs={self.inputs} outputs={self.outputs}>")


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, base_command, hints, requirements, inputs, outputs, stdout,
                 workflow_id, task_id=None):
        """Store a task description.

        Task ID should only be given as a parameter when reconstructing the Task object
        from the graph database.

        :param name: the task name
        :type name: str
        :param base_command: the base command to run for the task
        :type base_command: str or list of str
        :param hints: the task hints (optional requirements)
        :type hints: list of Hint
        :param requirements: the task requirements
        :type requirements: list of Requirement
        :param inputs: the task inputs
        :type inputs: list of StepInput
        :param outputs: the task outputs
        :type outputs: list of StepOutput
        :param stdout: the name of the file to which to redirect stdout
        :type stdout: str
        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param task_id: the task ID
        :type task_id: str
        """
        self.name = name
        self.base_command = base_command
        self.hints = hints
        self.requirements = requirements
        self.inputs = inputs
        self.outputs = outputs
        self.stdout = stdout
        self.workflow_id = workflow_id

        # Task ID as UUID if not given
        if task_id:
            self.id = task_id
        else:
            self.id = str(uuid4())

    def copy(self):
        """Make a copy of this task."""
        return Task(name=self.name, base_command=self.base_command,
                    hints=self.hints, requirements=self.requirements,
                    inputs=self.inputs, outputs=self.outputs,
                    stdout=self.stdout, workflow_id=self.workflow_id,
                    task_id=self.id)

    def __eq__(self, other):
        """Test the equality of two tasks.

        Task ID and dependencies do not factor into equality testing.
        :param other: the task with which to test equality
        :type other: instance of Task
        """
        id_sort = lambda i: i.id
        return bool(self.name == other.name and
                    self.base_command == other.base_command and
                    sorted(self.hints) == sorted(other.hints) and
                    sorted(self.requirements) == sorted(other.requirements) and
                    sorted(self.inputs, key=id_sort) == sorted(other.inputs, key=id_sort) and
                    sorted(self.outputs, key=id_sort) == sorted(other.outputs, key=id_sort) and
                    self.stdout == other.stdout)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: instance of Task
        """
        return bool(not self.__eq__(other))

    def __hash__(self):
        """Return the hash value for a task."""
        return hash((self.id, self.workflow_id, self.name))

    def __repr__(self):
        """Construct a task's string representation."""
        return (f"<Task id={self.id} name={self.name} base_command={self.base_command} "
                f"hints={self.hints} requirements = {self.requirements} "
                f"inputs={self.inputs} outputs={self.outputs} stdout={self.stdout} "
                f"workflow_id={self.workflow_id}>")

    @property
    def command(self):
        """Construct a task's command as a list.

        :rtype: list of str
        """
        positional_inputs = []
        nonpositional_inputs = []
        for input_ in self.inputs:
            if input_.value is None:
                raise ValueError("trying to construct command for task with missing input value")

            if input_.position is not None:
                positional_inputs.append(input_)
            else:
                nonpositional_inputs.append(input_)
        positional_inputs.sort(key=lambda i: i.position)

        if isinstance(self.base_command, list):
            command = self.base_command[:]
        else:
            command = [self.base_command]

        for input_ in positional_inputs:
            if input_.prefix is not None:
                command.append(input_.prefix)
            command.append(str(input_.value))
        for input_ in nonpositional_inputs:
            if input_.prefix is not None:
                command.append(input_.prefix)
            command.append(str(input_.value))

        return command
