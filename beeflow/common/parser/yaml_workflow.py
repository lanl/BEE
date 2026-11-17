"""Safe, versioned YAML front end for the BEE Python workflow API.

This module constructs workflow_api objects only. BeeParser remains responsible
for shared semantic validation and conversion into execution models.
"""

from dataclasses import fields
from pathlib import Path

import yaml

from beeflow.common import workflow_api as api


class _UniqueKeyLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
    """Safe YAML loader that rejects duplicate and non-string mapping keys."""

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, "expected a mapping node", node.start_mark
            )
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise api.WorkflowAPIError("YAML mapping keys must be strings")
            if key in mapping:
                raise api.WorkflowAPIError(
                    f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}"
                )
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _read_document(path):
    """Load one safe YAML document with source-aware error messages."""
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return yaml.load(stream, Loader=_UniqueKeyLoader)
    except (OSError, UnicodeError, yaml.YAMLError, api.WorkflowAPIError) as error:
        raise api.WorkflowAPIError(f"invalid YAML specification {path}: {error}") from None


def is_yaml_workflow(path):
    """Identify workflow YAML by its marker, not its filename or task fields.

    A present but unsupported bee_version is still a workflow document; the
    loader will report the version error instead of treating it as job inputs.
    """
    document = _read_document(path)
    return isinstance(document, dict) and "bee_version" in document


def _mapping(value, context, allowed=None):
    """Validate a mapping and optionally reject unknown field names."""
    if not isinstance(value, dict):
        raise api.WorkflowAPIError(f"{context} must be a mapping")
    if allowed is not None:
        unknown = value.keys() - set(allowed)
        if unknown:
            raise api.WorkflowAPIError(f"{context}: unknown fields {sorted(unknown)}")
    return value


def _name(value, context):
    """Validate a qualified-reference component."""
    if not isinstance(value, str) or not value.strip() or "/" in value:
        raise api.WorkflowAPIError(f"{context} must be a non-empty name without '/'")


def _strings(value, context):
    """Validate a mapping of non-empty names to strings."""
    for key, item in _mapping(value, context).items():
        if not isinstance(key, str) or not key.strip():
            raise api.WorkflowAPIError(f"{context} keys must be non-empty strings")
        if not isinstance(item, str):
            raise api.WorkflowAPIError(f"{context}.{key} must be a string")


def _task_options(options, name):
    """Check task structure before constructing an API task."""
    context = f"task {name}"
    allowed = {field.name for field in fields(api.Task)} - {"name"}
    options = dict(_mapping(options, context, allowed))
    commands = options.get("commands")
    commands = [commands] if isinstance(commands, str) else commands
    if not isinstance(commands, list) or not commands or any(
        not isinstance(command, str) or not command.strip() for command in commands
    ):
        raise api.WorkflowAPIError(f"{context}.commands must be a string or non-empty string list")
    for key in ("params", "inputs", "outputs", "scheduler_options"):
        if key in options:
            _mapping(options[key], f"{context}.{key}")
    for key, value in options.get("scheduler_options", {}).items():
        if value is not None and not isinstance(value, (str, int, float)):
            raise api.WorkflowAPIError(f"{context}.scheduler_options.{key} must be a scalar")
    if "outputs" in options:
        _strings(options["outputs"], f"{context}.outputs")
        for output_name in options["outputs"]:
            _name(output_name, f"{context} output name")
    for key in ("stdout", "stderr", "workdir", "pre_script", "post_script"):
        if key in options and not isinstance(options[key], str):
            raise api.WorkflowAPIError(f"{context}.{key} must be a string")
    dependencies = options.get("depends_on", [])
    if not isinstance(dependencies, list) or any(
        not isinstance(dependency, str) for dependency in dependencies
    ):
        raise api.WorkflowAPIError(f"{context}.depends_on must be a list of task names")
    if "resources" in options:
        resources = _mapping(options["resources"], f"{context}.resources",
                             {field.name for field in fields(api.Resources)})
        for key, value in resources.items():
            if key == "walltime":
                valid = isinstance(value, str)
            else:
                valid = isinstance(value, int) and not isinstance(value, bool) and value > 0
            if not valid:
                raise api.WorkflowAPIError(f"{context}.resources.{key} has an invalid value")
        options["resources"] = api.Resources(**resources)
    if "container" in options and not isinstance(options["container"], str):
        container = _mapping(options["container"], f"{context}.container",
                             {field.name for field in fields(api.Container)})
        if not isinstance(container.get("image"), str) or not container["image"].strip():
            raise api.WorkflowAPIError(f"{context}.container.image must be a non-empty string")
        if "bind_mounts" in container:
            _strings(container["bind_mounts"], f"{context}.container.bind_mounts")
        if "required" in container and not isinstance(container["required"], bool):
            raise api.WorkflowAPIError(f"{context}.container.required must be a boolean")
        options["container"] = api.Container(**container)
    return options


def _resolve_value(value, tasks, context):
    """Resolve an explicit output reference, leaving scalar values literal."""
    if isinstance(value, dict):
        _mapping(value, context, {"from"})
        reference = value.get("from")
        if not isinstance(reference, str) or reference.count("/") != 1:
            raise api.WorkflowAPIError(f"{context}: expected {{from: task/output}}")
        task_name, output_name = reference.split("/")
        if task_name not in tasks:
            raise api.WorkflowAPIError(f"{context}: unknown task {task_name!r}")
        return tasks[task_name].output(output_name)
    if not isinstance(value, (str, int, float)):
        raise api.WorkflowAPIError(f"{context}: expected a scalar or output reference")
    return value


def load_yaml_workflow(path):
    """Build API objects from a version-1 YAML workflow, resolving forward refs.

    Shared placeholder, reference and cycle validation is performed by BeeParser
    after loading. No YAML value is evaluated as Python code.
    """
    document = _mapping(_read_document(path), "workflow",
                        {"bee_version", "name", "description", "tasks"})
    version = document.get("bee_version")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise api.WorkflowAPIError("workflow requires bee_version: 1")
    name = document.get("name", Path(path).stem)
    description = document.get("description", "")
    if not isinstance(name, str) or not name.strip() or not isinstance(description, str):
        raise api.WorkflowAPIError(
            "workflow name and description must be strings; name is non-empty"
        )
    definitions = _mapping(document.get("tasks"), "workflow.tasks")
    workflow = api.Workflow(name, description)
    tasks = {}
    for task_name, options in definitions.items():
        _name(task_name, "task name")
        tasks[task_name] = workflow.add_task(name=task_name, **_task_options(options, task_name))
    for task in workflow.tasks:
        for field in ("inputs", "params"):
            values = getattr(task, field)
            setattr(task, field, {
                key: _resolve_value(value, tasks, f"task {task.name}.{field}.{key}")
                for key, value in values.items()
            })
        dependencies = []
        for dependency in task.depends_on or []:
            if dependency not in tasks:
                raise api.WorkflowAPIError(f"task {task.name}: unknown dependency {dependency!r}")
            dependencies.append(tasks[dependency])
        task.depends_on = dependencies
    return workflow
