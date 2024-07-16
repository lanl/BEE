"""Defines data structures for holding task and workflow data."""
from collections import namedtuple
from uuid import uuid4
from copy import deepcopy
import os

from beeflow.common.container_path import convert_path

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
# Task state update, usually sent from the task manager
TaskStateUpdate = namedtuple("TaskStateUpdate", ["wf_id", "task_id", "job_state",
                                                 "task_info", "output", "metadata"])


def generate_workflow_id():
    """Generate a unique workflow ID.

    :rtype: str
    """
    return uuid4().hex


class Workflow:
    """Data structure for holding data about a workflow."""

    def __init__(self, name, hints, requirements, inputs, outputs, workflow_id):
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
        self.id = workflow_id
        self.state = "SUBMITTED"

    def __eq__(self, other):
        """Test the equality of two workflows.

        Workflow ID and dependencies do not factor into equality testing.
        Currently, the code is boilerplate. We do not support multiple workflows.

        :param other: the workflow with which to test equality
        :type other: Workflow
        """
        if not isinstance(other, Workflow):
            return False

        def id_sort(i):
            return i.id

        return bool(self.name == other.name
                    and sorted(self.hints) == sorted(other.hints)
                    and sorted(self.requirements) == sorted(other.requirements)
                    and sorted(self.inputs, key=id_sort) == sorted(other.inputs, key=id_sort)
                    and sorted(self.outputs, key=id_sort) == sorted(other.outputs, key=id_sort))

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: Workflow
        """
        return bool(not self.__eq__(other))

    def __repr__(self):
        """Construct a workflow's string representation."""
        return (f"<Workflow id={self.id} name={self.name} hints={self.hints} "
                f"requirements = {self.requirements} inputs={self.inputs} outputs={self.outputs}>")


class Task:
    """Data structure for holding data about a single task."""

    def __init__(self, name, base_command, hints, requirements, inputs, outputs, stdout, stderr,
                 workflow_id, task_id=None, workdir=None):
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
        :param stderr: the name of the file to which to redirect stderr
        :type stderr: str
        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param task_id: the task ID
        :type task_id: str, optional
        :param workdir: the working directory from which to get and store data
        :type workdir: path, optional
        """
        self.name = name
        self.base_command = base_command
        self.hints = hints
        self.requirements = requirements
        self.inputs = inputs
        self.outputs = outputs
        self.stdout = stdout
        self.stderr = stderr
        self.workflow_id = workflow_id
        self.workdir = workdir

        # Task ID as UUID if not given
        if task_id is None:
            self.id = self.generate_task_id()
        else:
            self.id = task_id

    def generate_task_id(self):
        """Generate a unique task ID.

        :rtype: str
        """
        return uuid4().hex

    def copy(self, new_id=False):
        """Make a copy of this task.

        :param new_id: generate a new task ID
        :type new_id: bool
        :rtype: Task
        """
        task_id = self.generate_task_id() if new_id else self.id
        return Task(name=self.name, base_command=self.base_command,
                    hints=deepcopy(self.hints), requirements=deepcopy(self.requirements),
                    inputs=deepcopy(self.inputs), outputs=deepcopy(self.outputs),
                    stdout=self.stdout, stderr=self.stderr, workflow_id=self.workflow_id,
                    task_id=task_id, workdir=self.workdir)

    def get_requirement(self, req_type, req_param, default=None):
        """Get requirement from hints or requirements, prioritizing requirements over hints.

        :param req_type: the type of requirement (e.g. 'DockerRequirement')
        :type req_type: str
        :param req_param: the requirement parameter (e.g. 'dockerFile')
        :type req_param: str
        :param default: default value if the requirement is not found
        :type default: any

        When requirements are specified hints will be ignored.
        By default, tasks need not specify hints or requirements
        """
        requirements = dict(self.requirements)
        requirement = default
        # Get value if specified in requirements
        try:
            # Try to get Requirement
            requirement = requirements[req_type][req_param]
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No docker_req_param specified in task reqs.
            requirement = None
        # Ignore hints if requirements available
        if not requirement:
            hints = dict(self.hints)
            # Get value if specified in hints
            try:
                # Try to get Hints
                requirement = hints[req_type][req_param]
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No docker_req_param specified in task hints.
                requirement = default
        return requirement

    def get_full_requirement(self, req_type):
        """Get the full requirement (or hint) for this task, if it has one.

        :param req_type: the type of requirement (e.g. 'DockerRequirement')
        :type req_type: str

        This prefers requirements over hints. Returns None if no hint or
        requirement found.
        """
        result = None
        hints = dict(self.hints)
        try:
            # Try to get Hints
            hint = hints[req_type]
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No task hint specified.
            hint = None
        try:
            # Try to get Requirements
            req = self.requirements[req_type]
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No task requirement specified.
            req = None
        # Prefer requirements over hints
        if req:
            result = req
        elif hint:
            result = hint
        return result

    def __eq__(self, other):
        """Test the equality of two tasks.

        Task ID and dependencies do not factor into equality testing.
        :param other: the task with which to test equality
        :type other: Task
        :rtype: bool
        """
        if not isinstance(other, Task):
            return False

        def id_sort(i):
            return i.id

        return bool(self.name == other.name
                    and self.base_command == other.base_command
                    and sorted(self.hints) == sorted(other.hints)
                    and sorted(self.requirements) == sorted(other.requirements)
                    and sorted(self.inputs, key=id_sort) == sorted(other.inputs, key=id_sort)
                    and sorted(self.outputs, key=id_sort) == sorted(other.outputs, key=id_sort)
                    and self.stdout == other.stdout
                    and self.stderr == other.stderr
                    and self.workdir == other.workdir)

    def __ne__(self, other):
        """Test the inequality of two tasks.

        :param other: the task with which to test inequality
        :type other: Task
        :rtype: bool
        """
        return bool(not self.__eq__(other))

    def __hash__(self):
        """Return the hash value for a task.

        :rtype: int
        """
        return hash((self.id, self.workflow_id, self.name))

    def __repr__(self):
        """Construct a task's string representation.

        :rtype: str
        """
        return (f"<Task id={self.id} name={self.name} base_command={self.base_command} "
                f"hints={self.hints} requirements = {self.requirements} "
                f"inputs={self.inputs} outputs={self.outputs} stdout={self.stdout} "
                f"stderr={self.stderr} workflow_id={self.workflow_id}> ")

    @property
    def command(self):
        """Construct a task's command as a list.

        :rtype: list of str
        """
        positional_inputs = []
        nonpositional_inputs = []
        for input_ in self.inputs:
            if input_.value is None:
                raise ValueError(
                    ("trying to construct command for task with missing input value "
                     f"(id: {input_.id})")
                )

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

        # Append restart parameter and checkpoint file if CheckpointRequirement specified
        for hint in self.hints:
            if hint.class_ == "beeflow:CheckpointRequirement":
                if "bee_checkpoint_file__" in hint.params:
                    if "restart_parameters" in hint.params:
                        command.append(hint.params["restart_parameters"])
                    # Ignoring "container_path" for now
                    checkpoint_file = hint.params["bee_checkpoint_file__"]
                    # Charliecloud default bind mounts (this should taken from
                    # another requirement)
                    bind_mounts = {
                        os.getenv('HOME'): os.path.join('/home', os.getenv('USER')),
                    }
                    command.append(convert_path(checkpoint_file, bind_mounts))
                break

        return command
# Ignore C901: "'Task.command' is too complex" - right now this function is
#              under 50 lines of code. If we add any more lines I think it
#              might be best to break it up, but for now it seems fine.
# pylama:ignore=C901
