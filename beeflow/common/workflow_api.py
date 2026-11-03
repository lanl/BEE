"""BEE python workflow description API.

This module defines the new, CWL-free user-facing API for describing BEE
workflows. It is part of the pivot from CWL tracked in issue #1194.

A workflow is described by creating a Workflow object and adding Task objects
to it (see the migration plan in docs/cwl-migration-plan.md). Commands use
{name} placeholders that are filled in at execution time from the task's
params and inputs. Task inputs can be static values or references to the
outputs of other tasks. The BeeParser (beeflow.common.parser.BeeParser)
converts these objects directly into the Workflow and Task objects loaded
into the graph database by the WorkflowInterface.

Example:
    from beeflow.common.workflow_api import Workflow

    wf = Workflow(name="cat-grep", description="Cat a file then grep it")
    cat = wf.add_task(
        name="cat",
        commands=["cat {input_file}"],
        inputs={"input_file": "lorem.txt"},
        stdout="cat.txt",
        outputs={"contents": "cat.txt"},
    )
    wf.add_task(
        name="grep",
        commands=["grep {word} {text_file}"],
        params={"word": "Vivamus"},
        inputs={"text_file": cat.output("contents")},
        stdout="occur.txt",
        outputs={"occur": "occur.txt"},
    )
"""

import re
from dataclasses import dataclass, field

# Pattern used to find {name} placeholders in task commands
placeholder_pattern = re.compile(r"\{(\w+)\}")


class WorkflowAPIError(Exception):
    """Error raised for invalid python workflow specifications."""


@dataclass
class Resources:
    """HPC resource requirements for a task.

    nodes, ntasks, and tasks_per_node are recorded in the
    beeflow:MPIRequirement hint and walltime in the beeflow:SlurmRequirement
    hint (as timeLimit).
    """

    nodes: int = None
    ntasks: int = None
    tasks_per_node: int = None
    walltime: str = None


class OutputRef:
    """A reference to a named output of a task."""

    def __init__(self, task, output_name):
        """Create a reference to output_name of task."""
        self.task_name = task.name
        self.output_name = output_name

    @property
    def id(self):
        """Return the qualified task/output id of the reference.

        :rtype: str
        """
        return f"{self.task_name}/{self.output_name}"

    def __str__(self):
        """Return the qualified task/output id as a string."""
        return self.id

    def __repr__(self):
        """Return the output reference representation."""
        return f"<OutputRef {self.id}>"


@dataclass
class Container:
    """Container image settings for a task.

    image names a container image: either a registry reference to pull and
    build (for example "debian:12"), or the path of a local image file
    (.tar, .tar.gz, .sqfs, ...), which is used in place. bind_mounts maps
    host paths to paths inside the container. required makes the container
    mandatory: the task fails if the container cannot be provided, instead
    of falling back to the default environment when it can't.
    """

    image: str
    bind_mounts: dict = field(default_factory=dict)
    required: bool = False


@dataclass
class Task:
    """Represents a task in the new python workflow API.

    commands is one or more command strings. Multiple commands run in order
    and the next command runs only if the previous command succeeds
    (equivalent to joining them with ``&&``). A {name} placeholder in any
    command is replaced at execution time by the corresponding param or input.

    params holds task-local values used to fill {name} placeholders. inputs
    holds task inputs: a static value, or the result of another task's
    output() method to depend on that task. params/inputs names used with the
    same value in every task become workflow inputs (overridable through the
    job file); names declared with conflicting values stay task-local.

    depends_on lists other tasks of the workflow (the Task objects returned
    by add_task) that must reach a final state before this task starts, even
    when no data is passed between them; output() references already imply
    such a dependency.

    workdir sets the task's working directory, relative to the workflow
    workdir unless absolute. The directory is created when the task is
    submitted; files produced by the command and relative file paths in the
    command are resolved inside it.

    container runs the task in a container image: a plain string or a
    Container (see the Container dataclass for bind mounts and required).

    outputs maps output names to the files they collect. pre_script and
    post_script name script files (with a shebang line matching the shell)
    run before/after the command.
    """

    name: str
    commands: object
    params: dict = field(default_factory=dict)
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    resources: Resources = None
    scheduler_options: dict = None
    depends_on: list = None
    pre_script: str = None
    post_script: str = None
    stdout: str = None
    stderr: str = None
    workdir: str = None
    container: object = None

    def output(self, name):
        """Return a reference to one of this task's outputs.

        :param name: the output name
        :type name: str
        :rtype: OutputRef
        """
        if name not in self.outputs:
            raise WorkflowAPIError(
                    f"task {self.name} has no output {name!r} "
                    f"(outputs: {sorted(self.outputs)})"
                    )
        return OutputRef(self, name)

    def declared_values(self):
        """Return the declared params and inputs of the task.

        :rtype: dict
        """
        return {**self.params, **self.inputs}

    def placeholders(self):
        """Return the set of {name} placeholders used by the commands.

        :rtype: set of str
        """
        names = set()
        for command in self.command_list():
            names.update(placeholder_pattern.findall(command))
        return names

    def command_list(self):
        """Return the task commands as a list of command strings.

        :rtype: list of str
        """
        if isinstance(self.commands, str):
            return [self.commands]
        return list(self.commands)


class Workflow:
    """A BEE workflow: a name, a description, and a list of tasks."""

    def __init__(self, name, description="", tasks=None):
        """Create a workflow with the given name and description."""
        self.name = name
        self.description = description
        self.tasks = list(tasks) if tasks else []

    def add_task(self, task=None, **kwargs):
        """Add a task to the workflow and return it.

        Accepts either an existing Task object (add_task(task)) or Task
        keyword arguments (add_task(name=..., commands=...)).

        :rtype: Task
        """
        if task is not None and kwargs:
            raise WorkflowAPIError(
                    "add_task() accepts either a Task object or keyword "
                    "arguments, not both"
                    )
        if task is None:
            try:
                task = Task(**kwargs)
            except TypeError as err:
                raise WorkflowAPIError(f"invalid task: {err}") from None
        elif not isinstance(task, Task):
            raise WorkflowAPIError(
                    "add_task() requires a Task object or Task keyword arguments"
                    )
        self.tasks.append(task)
        return task
