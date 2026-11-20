"""Format registry, optional dependencies, and extension boundary regressions."""

from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from beeflow.common.object_models import Task, Workflow
from beeflow.common.parser import formats
from beeflow.common.parser.formats import FormatRegistry, WorkflowFormat, WorkflowFormatError


def _parse_custom(workflow_id, workflow_name, spec, **kwargs):
    """An extension returns execution models, not Python API authoring objects."""
    return Workflow(id=workflow_id, name=workflow_name or Path(spec).stem), [
        Task(name="custom", workflow_id=workflow_id, base_command=["echo", "custom"])
    ]


def test_builtin_discovery_without_executing_files(tmp_path):
    """Discovery uses suffixes/markers, preserving native-before-CWL precedence."""
    registry = formats.get_registry()
    (tmp_path / "old.cwl").write_text("not parsed during discovery", encoding="utf-8")
    assert registry.discover(tmp_path) == "old.cwl"
    (tmp_path / "workflow.yaml").write_text("bee_version: 1\ntasks: {}", encoding="utf-8")
    assert registry.discover(tmp_path) == "workflow.yaml"
    (tmp_path / "workflow.py").write_text("raise RuntimeError('never execute')", encoding="utf-8")
    with pytest.raises(WorkflowFormatError, match="Multiple workflow files"):
        registry.discover(tmp_path)


def test_cwl_adapter_preserves_positional_job(mocker, tmp_path):
    """Retain the parser calling convention as well as CWL path-derived names."""
    parse = mocker.patch("beeflow.common.parser.CwlParser.parse_workflow",
                         return_value=(Workflow(id="wf", name="legacy"), []))
    path = tmp_path / "legacy.cwl"
    formats.get_registry().resolve(path).parse_workflow("wf", None, path, "job.yml")
    parse.assert_called_once_with("wf", "legacy", str(path), job="job.yml", workdir=".", wf_path=".")


def test_cwl_adapter_accepts_paths():
    """Normalize Path objects before calling the historical string-only CWL loader."""
    root = Path(__file__).resolve().parents[2]
    path = root / "examples/cat-grep-tar/workflow.cwl"
    workflow, tasks = formats.get_registry().resolve(path).parse_workflow(
        "paths", None, path, job=path.parent / "input.yml",
    )
    assert workflow.name == "workflow"
    assert len(tasks) == 4


@pytest.mark.parametrize("suffix, content, expected", [
    (".py", "", "python"),
    (".PY", "", "python"),
    (".yaml", "bee_version: 99", "yaml"),
    (".yml", "bee_version: 1", "yaml"),
    (".cwl", "", "cwl"),
    (".yaml", "cwlVersion: v1.0", "cwl"),
    (".json", '{"cwlVersion": "v1.0"}', "cwl"),
    (".yaml", "message: hello", None),
    (".json", '{"message": "hello"}', None),
    (".txt", "hello", None),
])
def test_builtin_format_markers(tmp_path, suffix, content, expected):
    """CWL content detection does not need CWL packages, and job files stay inputs."""
    path = tmp_path / f"workflow{suffix}"
    path.write_text(content, encoding="utf-8")
    adapter = formats.get_registry().resolve(path, required=False)
    assert (adapter.name if adapter else None) == expected


def test_registry_errors(tmp_path):
    """Unknown, ambiguous and malformed formats have actionable errors."""
    registry = FormatRegistry()
    path = tmp_path / "workflow.custom"
    with pytest.raises(WorkflowFormatError, match="No workflow adapter"):
        registry.resolve(path)
    with pytest.raises(WorkflowFormatError, match="No workflow file"):
        registry.discover(tmp_path)
    with pytest.raises(WorkflowFormatError, match="Unknown workflow format"):
        registry.resolve(path, format_name="missing")
    for name in ("first", "second"):
        registry.register(WorkflowFormat(name, (".custom",), _parse_custom))
    with pytest.raises(WorkflowFormatError, match="Ambiguous workflow format"):
        registry.resolve(path)
    assert registry.resolve(path, format_name="first").name == "first"
    with pytest.raises(WorkflowFormatError, match="Duplicate workflow adapter"):
        registry.register(WorkflowFormat("first", (".other",), _parse_custom))


@pytest.mark.parametrize("adapter", [
    object(),
    WorkflowFormat("", (".custom",), _parse_custom),
    WorkflowFormat("bad", (), _parse_custom),
    WorkflowFormat("bad", [".custom"], _parse_custom),
    WorkflowFormat("bad", ("CUSTOM",), _parse_custom),
    WorkflowFormat("bad", (".tgz",), _parse_custom),
    WorkflowFormat("bad", (".",), _parse_custom),
    WorkflowFormat("bad", (".custom",), _parse_custom, discovery_priority="first"),
    WorkflowFormat("bad", (".custom",), None),
    WorkflowFormat("bad", (".custom",), _parse_custom, probe=False),
])
def test_invalid_adapter_registration(adapter):
    """Reject invalid descriptors before they reach discovery/submission."""
    with pytest.raises(WorkflowFormatError):
        FormatRegistry().register(adapter)


@pytest.mark.parametrize("factory", [False, True])
def test_installed_extension_entrypoint(mocker, tmp_path, factory):
    """Installed extensions may export either a descriptor or a factory."""
    adapter = WorkflowFormat("custom", (".custom",), _parse_custom)
    point = mocker.Mock(name="custom")
    point.name = "custom"
    point.load.return_value = (lambda: adapter) if factory else adapter
    entry_points = mocker.patch.object(formats, "entry_points", return_value=[point])
    registry = formats.get_registry()
    entry_points.assert_called_once_with(group="beeflow.workflow_formats")
    path = tmp_path / "workflow.custom"
    workflow, tasks = registry.resolve(path).parse_workflow("wf", "example", path)
    assert workflow.name == "example"
    assert tasks[0].name == "custom"


def test_parser_cli_uses_installed_adapter(mocker, monkeypatch, capsys, tmp_path):
    """The package parser CLI shares the registry rather than a suffix switch."""
    from beeflow.common.parser.parser import main  # pylint: disable=C0415
    point = mocker.Mock()
    point.name = "custom"
    point.load.return_value = WorkflowFormat("custom", (".custom",), _parse_custom)
    mocker.patch.object(formats, "entry_points", return_value=[point])
    path = tmp_path / "workflow.custom"
    path.write_text("custom specification", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["parser", str(path)])
    main()
    assert "name=custom" in capsys.readouterr().out


def test_parser_cli_unknown_format_is_concise(tmp_path):
    """Unknown formats should show a diagnostic, not a Python stack trace."""
    path = tmp_path / "workflow.unknown"
    path.write_text("unknown format", encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "beeflow.common.parser", str(path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "No workflow adapter recognizes" in result.stderr
    assert "Traceback" not in result.stderr


def test_broken_extension_is_reported(mocker):
    """An installed plugin failure must not silently change recognized formats."""
    point = mocker.Mock()
    point.name = "broken"
    point.load.side_effect = ImportError("missing plugin dependency")
    mocker.patch.object(formats, "entry_points", return_value=[point])
    with pytest.raises(WorkflowFormatError, match="broken.*missing plugin dependency"):
        formats.get_registry()


def test_extension_probe_failure(tmp_path):
    """Normalize extension probe errors rather than leaking a traceback to the CLI."""
    def fail(path):
        raise ValueError("invalid custom header")

    registry = FormatRegistry()
    registry.register(WorkflowFormat("custom", (".custom",), _parse_custom, probe=fail))
    with pytest.raises(WorkflowFormatError, match="custom probe failed.*invalid custom header"):
        registry.resolve(tmp_path / "workflow.custom")


def test_conflicting_yaml_markers(tmp_path):
    """A document claiming both formats must not silently pick a parser."""
    path = tmp_path / "ambiguous.yaml"
    path.write_text("bee_version: 1\ncwlVersion: v1.0\n", encoding="utf-8")
    with pytest.raises(WorkflowFormatError, match="Ambiguous workflow format"):
        formats.get_registry().resolve(path)


def test_adapter_execution_boundary():
    """Adapters cannot return unnormalized authoring objects or hide parser failures."""
    adapter = WorkflowFormat("bad", (".custom",), lambda *args: (object(), []))
    with pytest.raises(WorkflowFormatError, match="execution models"):
        adapter.parse_workflow("wf", "name", "workflow.custom")

    def fail(*args):
        raise WorkflowFormatError("already normalized")

    with pytest.raises(WorkflowFormatError, match="^already normalized$"):
        WorkflowFormat("bad", (".custom",), fail).parse_workflow("wf", "name", "file")


@pytest.mark.parametrize("content", ["[", "!!python/object/apply:os.system ['false']"])
def test_invalid_format_probe(tmp_path, content):
    """Content probes remain safe and report invalid YAML without executing it."""
    path = tmp_path / "bad.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(WorkflowFormatError, match="Cannot identify workflow"):
        formats.get_registry().resolve(path)


def test_python_yaml_without_optional_cwl_imports(tmp_path):
    """Block optional imports in a fresh process, including legacy API imports."""
    script = textwrap.dedent('''
        import importlib.abc
        from pathlib import Path
        import sys
        before = set(sys.modules)  # Some installations preload namespace-package stubs.

        class NoCwl(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if (fullname.split('.')[0] in {'cwl_utils', 'schema_salad', 'ruamel', 'cwltool'}
                        or fullname.startswith('beeflow.common.cwl')):
                    raise ModuleNotFoundError(fullname, name=fullname)

        sys.meta_path.insert(0, NoCwl())
        from beeflow.common.parser import BeeParser, CwlParser
        from beeflow.common.parser.formats import get_registry, WorkflowFormatError
        from beeflow.client import bee_client

        root = Path(sys.argv[1])
        yaml_path = root / 'workflow.yaml'
        yaml_path.write_text('bee_version: 1\\ntasks: {run: {commands: echo}}\\n')
        python_path = root / 'workflow.py'
        python_path.write_text(
            'from beeflow.common.workflow_api import Workflow\\n'
            'workflow = Workflow("native")\\n'
            'workflow.add_task(name="run", commands="echo")\\n'
        )
        registry = get_registry()
        for path in [yaml_path, python_path]:
            workflow, tasks = registry.resolve(path).parse_workflow('wf', None, path)
            assert tasks[0].name == 'run'
            assert bee_client._workflow_format(path).name in {'python', 'yaml'}
        try:
            registry.resolve(root / 'old.cwl').parse_workflow('wf', 'old', root / 'old.cwl')
        except WorkflowFormatError as error:
            assert 'hpc-beeflow[cwl]' in str(error), str(error)
        else:
            raise AssertionError('CWL unexpectedly worked without its dependencies')
        legacy_path = root / 'legacy.py'
        legacy_path.write_text('import ruamel.yaml\\n')
        try:
            registry.resolve(legacy_path).parse_workflow('wf', 'legacy', legacy_path)
        except WorkflowFormatError as error:
            assert 'hpc-beeflow[cwl]' in str(error), str(error)
        else:
            raise AssertionError('Legacy optional import unexpectedly worked')
        imported = [name for name in sys.modules if name not in before and name.startswith(
            ('cwl_utils', 'schema_salad', 'ruamel', 'beeflow.common.cwl'))]
        assert not imported, imported
    ''')
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
