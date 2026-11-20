"""Safe, layout-compatible archived workflow resource reading."""

import io
import tarfile

import pytest
import yaml

from beeflow.common.workflow_archive import WorkflowArchiveError, read_workflow_archive


def _archive(tmp_path, metadata, files=None, extra=None, layout="cwl_files"):
    filename = tmp_path / "renamed.tgz"
    files = files if files is not None else {"nested/main.py": b"workflow", "job.json": b"{}"}
    with tarfile.open(filename, "w:gz") as archive:
        data = metadata if isinstance(metadata, bytes) else yaml.safe_dump(metadata).encode()
        entries = {"original/submit_command_args.yaml": data}
        entries.update({f"original/{layout}/{name}": value for name, value in files.items()})
        for name, content in entries.items():
            member = tarfile.TarInfo(name)
            member.size = len(content)
            member.mode = 0o755
            archive.addfile(member, io.BytesIO(content))
        if extra is not None:
            archive.addfile(extra)
    destination = tmp_path / "resources"
    destination.mkdir()
    return filename, destination


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("layout", ["cwl_files", "workflow_files"])
def test_archive_metadata_and_nested_resources(tmp_path, legacy, layout):
    metadata = ({"main_cwl": "nested/main.py", "yaml": "job.json"} if legacy else
                {"spec_file": "nested/main.py", "job_file": "job.json", "format_name": "python"})
    filename, destination = _archive(tmp_path, metadata, layout=layout)
    result = read_workflow_archive(filename, destination)
    assert result["spec_file"] == str(destination / "nested/main.py")
    assert result["job_file"] == str(destination / "job.json")
    assert result["format_name"] == (None if legacy else "python")
    assert (destination / "nested/main.py").read_bytes() == b"workflow"
    assert (destination / "nested/main.py").stat().st_mode & 0o777 == 0o755


def test_old_archive_without_job(tmp_path):
    filename, destination = _archive(tmp_path, {"main_cwl": "nested/main.py"})
    assert read_workflow_archive(filename, destination)["job_file"] is None


def test_linked_metadata_is_rejected(tmp_path):
    filename = tmp_path / "linked.tgz"
    with tarfile.open(filename, "w:gz") as archive:
        member = tarfile.TarInfo("original/submit_command_args.yaml")
        member.type = tarfile.SYMTYPE
        member.linkname = "/outside"
        archive.addfile(member)
    with pytest.raises(WorkflowArchiveError, match="metadata must be a regular file"):
        read_workflow_archive(filename, tmp_path / "resources")


@pytest.mark.parametrize("metadata, message", [
    ({"spec_file": "../outside.py"}, "Unsafe archive path"),
    ({"spec_file": "/outside.py"}, "Unsafe archive path"),
    ({"spec_file": "nested\\main.py"}, "Invalid archive path"),
    ({"spec_file": "absent.py"}, "Missing archived spec_file"),
    ({"spec_file": "nested/main.py", "job_file": "absent.json"}, "Missing archived job_file"),
    ({"spec_file": "nested/main.py", "format_name": []}, "format_name must be a string"),
    ({}, "Invalid archive path"),
    ([], "must be a mapping"),
    (b"!!python/object/apply:os.system ['false']", "Cannot read workflow archive"),
    (b"[", "Cannot read workflow archive"),
])
def test_invalid_archive_metadata(tmp_path, metadata, message):
    filename, destination = _archive(tmp_path, metadata)
    with pytest.raises(WorkflowArchiveError, match=message):
        read_workflow_archive(filename, destination)


@pytest.mark.parametrize("kind", ["traversal", "absolute", "symlink", "hardlink", "device",
                                 "duplicate", "metadata", "layout"])
def test_unsafe_or_ambiguous_archive(tmp_path, kind):
    member = tarfile.TarInfo("original/cwl_files/unsafe")
    if kind == "traversal":
        member.name = "original/cwl_files/../../escape"
    elif kind == "absolute":
        member.name = "/escape"
    elif kind == "symlink":
        member.type = tarfile.SYMTYPE
        member.linkname = "/outside"
    elif kind == "hardlink":
        member.type = tarfile.LNKTYPE
        member.linkname = "original/cwl_files/nested/main.py"
    elif kind == "device":
        member.type = tarfile.CHRTYPE
    elif kind == "duplicate":
        member.name = "original/cwl_files/nested/main.py"
    elif kind == "metadata":
        member.name = "second/submit_command_args.yaml"
    else:
        member.name = "original/workflow_files/other.py"
    filename, destination = _archive(tmp_path, {"spec_file": "nested/main.py"}, extra=member)
    with pytest.raises(WorkflowArchiveError):
        read_workflow_archive(filename, destination)
