"""Read archived submission metadata while retaining legacy archive layouts."""

from pathlib import Path, PurePosixPath
import shutil
import tarfile

import yaml


class WorkflowArchiveError(ValueError):
    """An archive has missing, ambiguous or unsafe workflow metadata/resources."""


def _relative(value):
    """Require portable relative paths with no parent traversal."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise WorkflowArchiveError(f"Invalid archive path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise WorkflowArchiveError(f"Unsafe archive path: {value!r}")
    return path


def read_workflow_archive(filename, destination):
    """Extract only workflow resources, returning canonical submission metadata.

    Locate the root from metadata, not the tarball filename. Existing cwl_files
    directories and newer workflow_files directories are both accepted. Never
    extract links, devices, unrelated outputs or arbitrary YAML Python objects.
    The destination must be a fresh, caller-owned temporary directory.
    """
    try:
        with tarfile.open(filename) as archive:
            members = {}
            for member in archive.getmembers():
                path = _relative(member.name)
                if path in members:
                    raise WorkflowArchiveError(f"Duplicate archive path: {path}")
                members[path] = member
            metadata = [path for path in members if path.name == "submit_command_args.yaml"]
            if len(metadata) != 1:
                raise WorkflowArchiveError("Expected exactly one submit_command_args.yaml")
            member = members[metadata[0]]
            if not member.isfile():
                raise WorkflowArchiveError("Submission metadata must be a regular file")
            with archive.extractfile(member) as stream:
                command = yaml.safe_load(stream)
            if not isinstance(command, dict):
                raise WorkflowArchiveError("Submission metadata must be a mapping")
            root = metadata[0].parent
            layouts = [root / name for name in ("workflow_files", "cwl_files")
                       if any(path.is_relative_to(root / name) for path in members)]
            if len(layouts) != 1:
                raise WorkflowArchiveError("Expected one workflow_files or cwl_files directory")
            resources = layouts[0]
            for path, member in members.items():
                if not path.is_relative_to(resources) or path == resources:
                    continue
                target = Path(destination) / str(path.relative_to(resources))
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as source, target.open("xb") as output:
                        shutil.copyfileobj(source, output)
                    target.chmod(member.mode & 0o777)
                else:
                    raise WorkflowArchiveError(
                        f"Unsupported archive resource (link/device): {path}"
                    )
            result = {}
            for canonical, legacy in (("spec_file", "main_cwl"), ("job_file", "yaml")):
                value = command.get(canonical, command.get(legacy))
                if not value and canonical == "job_file":
                    result[canonical] = None
                    continue
                relative = _relative(value)
                target = Path(destination) / str(relative)
                if not target.is_file():
                    raise WorkflowArchiveError(f"Missing archived {canonical}: {relative}")
                result[canonical] = str(target)
            result["format_name"] = command.get("format_name")
            if result["format_name"] is not None and not isinstance(result["format_name"], str):
                raise WorkflowArchiveError("format_name must be a string")
            return result
    except (OSError, tarfile.TarError, yaml.YAMLError) as error:
        raise WorkflowArchiveError(f"Cannot read workflow archive: {error}") from error
