"""YAML schema, Python parity, and execution regression tests."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from beeflow.common import workflow_api as api
from beeflow.common.db.gdb_db import SQL_GDB
from beeflow.common.parser import BeeParseError, BeeParser
from beeflow.common.parser.parser import main as parser_main
from beeflow.common.parser.yaml_workflow import is_yaml_workflow
from beeflow.common.worker.simple_worker import SimpleWorker


def _write(tmp_path, document):
    path = tmp_path / "workflow.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return path


def _document(**options):
    return {"bee_version": 1, "tasks": {"run": {"commands": "echo hi", **options}}}


def test_yaml_python_parity(tmp_path):
    """Every task option maps to the same execution models as Python objects."""
    python = api.Workflow("parity", "Equivalent specifications")
    for script in ("pre.sh", "post.sh"):
        (tmp_path / script).write_text("#!/bin/bash\necho script\n", encoding="utf-8")
    setup = api.Task(name="setup", commands="echo setup", outputs={"text": "setup.txt"})
    python.add_task(
        name="run", commands=["cat {text}", "echo {word}"],
        params={"word": "hello"}, inputs={"text": setup.output("text")},
        outputs={"result": "result.txt"}, depends_on=[setup],
        resources=api.Resources(nodes=1, ntasks=2, tasks_per_node=2, walltime="00:10:00"),
        scheduler_options={"partition": "debug"},
        container=api.Container("debian:12", {"/host": "/data"}, required=True),
        workdir="run", stdout="out.txt", stderr="err.txt",
        pre_script=str(tmp_path / "pre.sh"), post_script=str(tmp_path / "post.sh"),
    )
    python.add_task(setup)
    path = _write(tmp_path, {
        "bee_version": 1, "name": "parity", "description": "Equivalent specifications",
        "tasks": {
            "run": {
                "commands": ["cat {text}", "echo {word}"], "params": {"word": "hello"},
                "inputs": {"text": {"from": "setup/text"}},
                "outputs": {"result": "result.txt"}, "depends_on": ["setup"],
                "resources": {"nodes": 1, "ntasks": 2, "tasks_per_node": 2,
                              "walltime": "00:10:00"},
                "scheduler_options": {"partition": "debug"},
                "container": {"image": "debian:12", "bind_mounts": {"/host": "/data"},
                              "required": True},
                "workdir": "run", "stdout": "out.txt", "stderr": "err.txt",
                "pre_script": "pre.sh", "post_script": "post.sh",
            },
            "setup": {"commands": "echo setup", "outputs": {"text": "setup.txt"}},
        },
    })
    expected_wf, expected_tasks = BeeParser().parse_workflow("wf", None, python,
                                                            workdir=str(tmp_path))
    actual_wf, actual_tasks = BeeParser().parse_workflow("wf", None, path,
                                                        workdir=str(tmp_path))
    assert actual_wf.model_dump(exclude={"spec_file", "format_name"}) == expected_wf.model_dump(
        exclude={"spec_file", "format_name"}
    )
    assert [task.model_dump(exclude={"id"}) for task in actual_tasks] == [
        task.model_dump(exclude={"id"}) for task in expected_tasks
    ]


def test_yaml_defaults_and_job_override(tmp_path):
    """A standalone spec needs no job file, but accepts optional value overrides."""
    path = _write(tmp_path, _document(commands="echo {message}", inputs={"message": "old"}))
    job = tmp_path / "job.yml"
    job.write_text("message: replacement\n", encoding="utf-8")
    workflow, _ = BeeParser().parse_workflow("wf", None, path, job=str(job))
    assert workflow.name == "workflow"
    assert workflow.inputs[0].value == "replacement"
    assert is_yaml_workflow(path)
    assert not is_yaml_workflow(job)


@pytest.mark.parametrize("document, message", [
    ({}, "bee_version"),
    ({"bee_version": True, "tasks": {}}, "bee_version"),
    ({"bee_version": 2, "tasks": {}}, "bee_version"),
    ({"bee_version": 1, "tasks": {}, "extra": 0}, "unknown fields"),
    ({"bee_version": 1, "name": 0, "tasks": {}}, "name and description"),
    ({"bee_version": 1, "tasks": {"bad/name": {"commands": "echo"}}}, "without '/'"),
    ({"bee_version": 1, "tasks": []}, "must be a mapping"),
    ({"bee_version": 1, "tasks": {}}, "does not define any tasks"),
    (_document(command="echo typo"), "unknown fields"),
    (_document(commands=[]), "commands"),
    (_document(commands=42), "commands"),
    (_document(commands=["echo ok", None]), "commands"),
    (_document(inputs=[]), "must be a mapping"),
    (_document(inputs={"bad": [1, 2]}), "expected a scalar"),
    (_document(inputs={"bad": {"from": "missing"}}), "expected.*from"),
    (_document(inputs={"bad": {"from": "other/out"}}), "unknown task"),
    (_document(inputs={"bad": {"from": "run/missing"}}), "no output"),
    (_document(inputs={"bad": {"from": "run/out", "typo": 1}}), "unknown fields"),
    (_document(depends_on="run"), "list of task names"),
    (_document(depends_on=["absent"]), "unknown dependency"),
    (_document(depends_on=["run"]), "dependency cycle"),
    (_document(commands="echo {missing}"), "no matching param"),
    (_document(resources={"nodes": True}), "invalid value"),
    (_document(resources={"nodes": 0}), "invalid value"),
    (_document(resources={"typo": 1}), "unknown fields"),
    (_document(scheduler_options={"partition": []}), "must be a scalar"),
    (_document(container={"required": True}), "container.image"),
    (_document(container={"image": "debian", "required": "yes"}), "boolean"),
    (_document(container={"image": "debian", "bind_mounts": []}), "must be a mapping"),
    (_document(container={"image": "debian", "bind_mounts": {"": "/data"}}), "non-empty"),
    (_document(workdir=12), "must be a string"),
    (_document(outputs={"out": 12}), "must be a string"),
])
def test_invalid_yaml_schema(tmp_path, document, message):
    """Invalid structures report parser errors instead of internal exceptions."""
    with pytest.raises(BeeParseError, match=message):
        BeeParser().parse_workflow("wf", None, _write(tmp_path, document))


@pytest.mark.parametrize("text", [
    "bee_version: 1\nbee_version: 1\ntasks: {}\n",
    "bee_version: 1\ntasks:\n  run: {commands: true}\n  run: {commands: false}\n",
    "bee_version: 1\ntasks: {run: {commands: echo, commands: false}}\n",
    "!!python/object/apply:os.system ['touch should-not-exist']",
    "bee_version: [",
    "bee_version: 1\n---\nbee_version: 1\n",
    "bee_version: 1\ntasks: {12: {commands: echo}}",
    "!!map [1]",
])
def test_unsafe_duplicate_or_malformed_yaml(tmp_path, text):
    """Reject unsafe tags, duplicate keys, non-string keys and broken syntax."""
    path = tmp_path / "bad.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(BeeParseError, match="invalid YAML"):
        BeeParser().parse_workflow("wf", None, path)


def test_mixed_cycle_and_literal_reference(tmp_path):
    """Data and ordering references participate in the shared cycle validator."""
    path = _write(tmp_path, {
        "bee_version": 1, "tasks": {
            "first": {"commands": "echo {literal}", "inputs": {"literal": "second/out"},
                      "outputs": {"out": "out.txt"}, "depends_on": ["second"]},
            "second": {"commands": "echo {data}",
                       "inputs": {"data": {"from": "first/out"}}},
        },
    })
    with pytest.raises(BeeParseError, match="dependency cycle"):
        BeeParser().parse_workflow("wf", None, path)


@pytest.mark.parametrize("container", ["debian:12", {"image": "/images/local.sqfs"}])
def test_container_hints_and_literal_values(tmp_path, container):
    """Shorthand/default containers are hints; reference-like strings stay literal."""
    path = _write(tmp_path, _document(container=container, inputs={"text": "other/out"}))
    _, tasks = BeeParser().parse_workflow("wf", None, path)
    task = tasks[0]
    assert task.requirements == []
    assert task.hints[0].class_ == "DockerRequirement"
    assert task.inputs[0].default == "other/out"
    assert task.inputs[0].source == "text"
    assert task.depends_on == []


def test_yaml_data_cycle(tmp_path):
    """Pure data-reference cycles also reach the shared cycle validator."""
    path = _write(tmp_path, {"bee_version": 1, "tasks": {
        "a": {"commands": "echo {data}", "inputs": {"data": {"from": "b/out"}},
              "outputs": {"out": "a.txt"}},
        "b": {"commands": "echo {data}", "inputs": {"data": {"from": "a/out"}},
              "outputs": {"out": "b.txt"}},
    }})
    with pytest.raises(BeeParseError, match="dependency cycle"):
        BeeParser().parse_workflow("wf", None, path)


def test_yaml_local_worker_execution(tmp_path):
    """One YAML file can drive real local commands via existing execution models."""
    path = _write(tmp_path, {
        "bee_version": 1, "tasks": {
            "setup": {"commands": ["printf ready > ready.txt", "true"]},
            "run": {"commands": ["test -f ../ready.txt", "printf done > result.txt"],
                    "depends_on": ["setup"], "workdir": "results",
                    "outputs": {"result": "result.txt"}},
        },
    })
    workflow, tasks = BeeParser().parse_workflow("wf", None, path, workdir=str(tmp_path))
    graph = SQL_GDB(str(tmp_path / "graph.db"))
    graph.create_workflow(workflow)
    for task in reversed(tasks):
        graph.create_task(task)
        graph.add_dependencies(task)
    worker = SimpleWorker(bee_workdir=str(tmp_path / "bee"), container_runtime="Charliecloud")
    graph.set_runnable_tasks_to_ready(workflow.id)
    assert graph.get_task_state(tasks[1].id) == "WAITING"
    for task in tasks:
        loaded = graph.get_task(task.id)
        assert loaded.state == "READY"
        job_id, _, info = worker.submit_task(loaded)
        os.waitpid(job_id, 0)
        state, _ = worker.query_task(job_id, job_info=info)
        assert state == "COMPLETED"
        graph.set_task_state(task.id, state)
        graph.set_runnable_tasks_to_ready(workflow.id)
    assert (tmp_path / "results" / "result.txt").read_text() == "done"


def test_yaml_example_parser_cli(monkeypatch, capsys):
    """The shipped single-file example parses through the documented CLI path."""
    path = Path(__file__).resolve().parents[2] / "examples/yaml-workflow/workflow.yaml"
    monkeypatch.setattr(sys, "argv", ["parser", str(path)])
    parser_main()
    output = capsys.readouterr().out
    assert "Parsed workflow:" in output
    assert "source='message/contents'" in output
    assert "name=finish" in output


@pytest.mark.parametrize("suffix", ["yaml", "py"])
def test_package_entry_point_has_no_runpy_warning(tmp_path, suffix):
    """Exercise the real module entry point with runtime warnings made fatal."""
    path = tmp_path / f"workflow.{suffix}"
    if suffix == "yaml":
        content = "bee_version: 1\ntasks: {hello: {commands: echo}}\n"
    else:
        content = (
            "from beeflow.common.workflow_api import Workflow\n"
            "workflow = Workflow('hello')\n"
            "workflow.add_task(name='hello', commands='echo')\n"
        )
    path.write_text(content, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-W", "error::RuntimeWarning", "-m", "beeflow.common.parser", str(path)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Parsed workflow:" in result.stdout
    assert "RuntimeWarning" not in result.stderr
