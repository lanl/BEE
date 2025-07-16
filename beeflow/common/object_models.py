"""Defines data structures for holding task and workflow data using pydantic models."""

from pathlib import Path
from uuid import uuid4
from copy import deepcopy
import os
from typing import Any, Optional
from pydantic import BaseModel, model_validator

from beeflow.common.container_path import convert_path


class InputParameter(BaseModel):
    """Pydantic model for InputParameter."""

    id: str
    type: str
    value: Any


class OutputParameter(BaseModel):
    """Pydantic model for OutputParameter."""

    id: str
    type: str
    value: Optional[Any] = None
    source: str


class StepInput(BaseModel):
    """Pydantic model for StepInput."""

    id: str
    type: str
    value: Optional[Any] = None
    default: Optional[Any] = None
    source: Optional[str] = None
    prefix: Optional[str] = None
    position: Optional[int] = None
    value_from: Optional[str] = None


class StepOutput(BaseModel):
    """Pydantic model for StepOutput."""

    id: str
    type: str
    value: Optional[Any] = None
    glob: Optional[str] = None


class Requirement(BaseModel):
    """Pydantic model for Requirement."""

    class_: str
    params: dict

    def __iter__(self):
        """Make Requirement iterable for dict conversion."""
        yield self.class_
        yield self.params


class Hint(BaseModel):
    """Pydantic model for Hint."""

    class_: str
    params: dict

    def __iter__(self):
        """Make Hint iterable for dict conversion."""
        yield self.class_
        yield self.params


def generate_workflow_id():
    """Generate a unique workflow ID.

    :rtype: str
    """
    return uuid4().hex


class Workflow(BaseModel):
    """Data structure for holding data about a workflow."""

    name: str
    hints: Optional[list[Hint]] = []
    requirements: Optional[list[Requirement]] = []
    inputs: list[InputParameter] = []
    outputs: list[OutputParameter] = []
    id: str
    state: Optional[str] = "Initializing"

    def __eq__(self, other):
        """Test the equality of two workflows.

        Workflow ID and dependencies do not factor into equality testing.
        Currently, the code is boilerplate. We do not support multiple workflows.

        :param other: the workflow with which to test equality
        :type other: Workflow
        """
        if not isinstance(other, Workflow):
            return False

        if not (self.name == other.name and self.state == other.state):
            return False

        # Convert collections to sets of string representations
        return (
            set(repr(h) for h in self.hints) == set(repr(h) for h in other.hints)
            and set(repr(r) for r in self.requirements)
            == set(repr(r) for r in other.requirements)
            and set(repr(i) for i in self.inputs) == set(repr(i) for i in other.inputs)
            and set(repr(o) for o in self.outputs)
            == set(repr(o) for o in other.outputs)
        )

    def __ne__(self, other):
        """Test the inequality of two workflows.

        :param other: the workflow with which to test inequality
        :type other: Workflow
        """
        return bool(not self.__eq__(other))

    def __repr__(self):
        """Construct a workflow's string representation."""
        return (
            f"<Workflow id={self.id} name={self.name} hints={self.hints} "
            f"requirements = {self.requirements} inputs={self.inputs} outputs={self.outputs}>"
        )


def get_requirement(requirements, hints, req_type, req_param, default=None):
    """Get requirement from hints or requirements, prioritizing requirements over hints.

    :param requirements: list of requirements
    :type requirements: list
    :param hints: list of hints
    :type hints: list
    :param req_type: the type of requirement (e.g. 'DockerRequirement')
    :type req_type: str
    :param req_param: the requirement parameter (e.g. 'dockerFile')
    :type req_param: str
    :param default: default value if the requirement is not found
    :type default: any

    When requirements are specified hints will be ignored.
    By default, tasks need not specify hints or requirements
    """
    requirements = dict(requirements)
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
        hints = dict(hints)
        # Get value if specified in hints
        try:
            # Try to get Hints
            requirement = hints[req_type][req_param]
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No docker_req_param specified in task hints.
            requirement = default
    return requirement


class Task(BaseModel):
    """Data structure for holding data about a single task."""

    name: str
    base_command: str | list[str]
    hints: Optional[list[Hint]] = []
    requirements: Optional[list[Requirement]] = []
    inputs: list[StepInput] = []
    outputs: list[StepOutput] = []
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    workflow_id: str
    workdir: Optional[str | Path | os.PathLike] = None
    id: Optional[str] = None
    state: Optional[str] = ""
    metadata: Optional[dict] = {}

    @model_validator(mode="before")
    def generate_id_if_missing(cls, data):  # pylint: disable=E0213
        """Generate a unique ID for the task if it is not provided."""
        if isinstance(data, dict) and "id" not in data:
            data["id"] = uuid4().hex
        return data

    def copy(
        self, *, deep=True, update=None, include=None, exclude=None  # pylint: disable=W0613
    ):
        """Make a copy of this task.

        :param deep: Whether to make a deep copy
        :param update: Values to update in the copy
        :param include: Fields to include
        :param exclude: Fields to exclude
        :rtype: Task
        """
        # Ignore the parent implementation but keep the signature compatible
        task_id = uuid4().hex if update and update.get("new_id", False) else self.id

        # Your existing implementation with the proper deep copy logic
        copy_method = deepcopy if deep else lambda x: x

        task = Task(
            name=self.name,
            base_command=self.base_command,
            hints=copy_method(self.hints),
            requirements=copy_method(self.requirements),
            inputs=copy_method(self.inputs),
            outputs=copy_method(self.outputs),
            stdout=self.stdout,
            stderr=self.stderr,
            workflow_id=self.workflow_id,
            id=task_id,
            workdir=self.workdir,
        )

        # Apply any updates if provided
        if update:
            for key, value in update.items():
                if key != "new_id":  # Skip our special parameter
                    setattr(task, key, value)

        return task

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
        return get_requirement(
            self.requirements, self.hints, req_type, req_param, default
        )

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

        if not (
            self.name == other.name
            and self.base_command == other.base_command
            and self.stdout == other.stdout
            and self.stderr == other.stderr
            and self.workdir == other.workdir
        ):
            return False

        # Convert collections to sets of string representations
        return (
            set(repr(h) for h in self.hints) == set(repr(h) for h in other.hints)
            and set(repr(r) for r in self.requirements)
            == set(repr(r) for r in other.requirements)
            and set(repr(i) for i in self.inputs) == set(repr(i) for i in other.inputs)
            and set(repr(o) for o in self.outputs)
            == set(repr(o) for o in other.outputs)
        )

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
        return (
            f"<Task id={self.id} name={self.name} base_command={self.base_command} "
            f"hints={self.hints} requirements = {self.requirements} "
            f"inputs={self.inputs} outputs={self.outputs} stdout={self.stdout} "
            f"stderr={self.stderr} workflow_id={self.workflow_id}> "
        )

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
                    (
                        "trying to construct command for task with missing input value "
                        f"(id: {input_.id})"
                    )
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
                        os.getenv("HOME"): os.path.join("/home", os.getenv("USER")),
                    }
                    command.append(convert_path(checkpoint_file, bind_mounts))
                    if "add_parameters" in hint.params:
                        command.append(hint.params["add_parameters"])
                break

        return command
