"""Workflow-format adapters and discovery, independent of optional CWL packages.

Adapters return the common execution Workflow and Task models. Installing an
adapter is a trust decision: entry points load Python code, unlike YAML data.
"""

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import Callable

import yaml

from beeflow.common.object_models import Task, Workflow


class WorkflowFormatError(Exception):
    """An unknown, ambiguous, unavailable or invalid workflow format."""


def _yaml_marker(path, marker):
    """Identify YAML/JSON documents without importing a format's dependencies."""
    try:
        with path.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise WorkflowFormatError(f"Cannot identify workflow file {path}: {error}") from None
    return isinstance(document, dict) and marker in document


def _bee_yaml(path):
    """Identify BEE YAML; full strict validation happens in its parser."""
    return _yaml_marker(path, "bee_version")


def _cwl(path):
    """Recognize conventional CWL files and explicitly marked YAML/JSON CWL."""
    return path.suffix.lower() == ".cwl" or _yaml_marker(path, "cwlVersion")


def _parse_bee(workflow_id, workflow_name, spec, job=None, workdir=".", wf_path="."):
    """Load the built-in parser only when parsing is requested."""
    parser = import_module("beeflow.common.parser.parser").BeeParser()
    return parser.parse_workflow(workflow_id, workflow_name, spec,
                                 job=str(job) if job is not None else None,
                                 workdir=workdir, wf_path=wf_path)


def _parse_cwl(workflow_id, workflow_name, spec, job=None, workdir=".", wf_path="."):
    """Use the compatibility parser, whose optional imports happen at parse time."""
    parser = import_module("beeflow.common.parser.parser").CwlParser()
    return parser.parse_workflow(
        workflow_id, workflow_name or Path(spec).stem, str(spec),
        job=str(job) if job is not None else None, workdir=workdir, wf_path=wf_path,
    )


@dataclass(frozen=True)
class WorkflowFormat:
    """Read adapter contract, usable by built-ins and installed extensions.

    parse has the same signature as BeeParser.parse_workflow and returns a
    (Workflow, list[Task]) pair. probe is an optional cheap content discriminator;
    it must not execute the specification. Lower discovery_priority wins only
    during directory discovery, never to hide ambiguity within a file format.
    bundle_directory packages neighbors of a direct-file submission (e.g. CWL
    run files). Optional dependencies must be imported inside parse, not probe.
    """

    name: str
    extensions: tuple[str, ...]
    parse: Callable
    probe: Callable | None = None
    discovery_priority: int = 0
    bundle_directory: bool = False

    def recognizes(self, path):
        """Return whether this adapter recognizes a file without parsing it."""
        path = Path(path)
        try:
            return path.suffix.lower() in self.extensions and (
                self.probe is None or self.probe(path)
            )
        except WorkflowFormatError:
            raise
        except Exception as error:  # pylint: disable=W0718
            raise WorkflowFormatError(f"{self.name} probe failed for {path}: {error}") from error

    def parse_workflow(self, *args, **kwargs):
        """Normalize parser failures and enforce the common execution boundary."""
        try:
            workflow, tasks = self.parse(*args, **kwargs)
            if not isinstance(workflow, Workflow) or not isinstance(tasks, list) or any(
                not isinstance(task, Task) for task in tasks
            ):
                raise TypeError("expected (Workflow, list[Task]) execution models")
            workflow.format_name = self.name
            return workflow, tasks
        except WorkflowFormatError:
            raise
        except Exception as error:  # pylint: disable=W0718
            raise WorkflowFormatError(f"{self.name} workflow: {error}") from error


class FormatRegistry:
    """Resolve formats and directory candidates without executing workflows."""

    def __init__(self):
        self.formats = {}

    def register(self, adapter):
        """Register a format; do not allow extensions to replace built-ins silently."""
        if not isinstance(adapter, WorkflowFormat):
            raise WorkflowFormatError("Workflow adapters must be WorkflowFormat instances")
        if not isinstance(adapter.name, str) or not adapter.name.strip():
            raise WorkflowFormatError("Workflow adapter names must be non-empty strings")
        if adapter.name in self.formats:
            raise WorkflowFormatError(f"Duplicate workflow adapter name: {adapter.name}")
        if not isinstance(adapter.extensions, tuple) or not adapter.extensions or any(
            not isinstance(suffix, str) or not suffix.startswith(".") or suffix != suffix.lower()
            or suffix in (".", ".tgz") or "/" in suffix for suffix in adapter.extensions
        ):
            raise WorkflowFormatError(
                "Adapter extensions must be a non-empty tuple of lowercase suffixes, not .tgz"
            )
        if not callable(adapter.parse) or (
            adapter.probe is not None and not callable(adapter.probe)
        ):
            raise WorkflowFormatError("Adapter parse/probe must be callable")
        if not isinstance(adapter.discovery_priority, int) or not isinstance(
            adapter.bundle_directory, bool
        ):
            raise WorkflowFormatError(
                "Adapter priority must be an integer and bundle flag boolean"
            )
        self.formats[adapter.name] = adapter

    def resolve(self, path, format_name=None, required=True):
        """Select one adapter, or return None for a non-workflow candidate."""
        if format_name is not None:
            try:
                return self.formats[format_name]
            except KeyError:
                raise WorkflowFormatError(f"Unknown workflow format: {format_name}") from None
        matches = [adapter for adapter in self.formats.values() if adapter.recognizes(path)]
        if len(matches) > 1:
            raise WorkflowFormatError(
                f"Ambiguous workflow format for {path}: {', '.join(a.name for a in matches)}"
            )
        if matches:
            return matches[0]
        if required:
            raise WorkflowFormatError(f"No workflow adapter recognizes {path}")
        return None

    def discover(self, directory):
        """Find one main file, preferring native BEE formats over legacy CWL."""
        candidates = []
        for path in sorted(Path(directory).iterdir()):
            if path.is_file():
                adapter = self.resolve(path, required=False)
                if adapter is not None:
                    candidates.append((adapter.discovery_priority, path.name))
        if not candidates:
            raise WorkflowFormatError(f"No workflow file found in {directory}; use --main-cwl")
        priority = min(item[0] for item in candidates)
        preferred = [name for rank, name in candidates if rank == priority]
        if len(preferred) > 1:
            raise WorkflowFormatError(
                f"Multiple workflow files found in {directory}: {', '.join(preferred)}; "
                "specify the main one with --main-cwl"
            )
        return preferred[0]


def get_registry():
    """Build the registry, including installed beeflow.workflow_formats entry points.

    Entry points export a WorkflowFormat instance or a no-argument factory.
    A broken installed extension is reported explicitly, not silently ignored.
    """
    registry = FormatRegistry()
    for adapter in (
        WorkflowFormat("python", (".py",), _parse_bee),
        WorkflowFormat("yaml", (".yaml", ".yml"), _parse_bee, probe=_bee_yaml),
        WorkflowFormat("cwl", (".cwl", ".yaml", ".yml", ".json"), _parse_cwl,
                       probe=_cwl, discovery_priority=10, bundle_directory=True),
    ):
        registry.register(adapter)
    for point in entry_points(group="beeflow.workflow_formats"):
        try:
            adapter = point.load()
            registry.register(adapter if isinstance(adapter, WorkflowFormat) else adapter())
        except Exception as error:  # pylint: disable=W0718
            raise WorkflowFormatError(
                f"Cannot load workflow adapter {point.name}: {error}"
            ) from error
    return registry
