"""Tests for the BEE python workflow specification parser (BeeParser)."""

import textwrap

import pytest

from beeflow.common import workflow_api
from beeflow.common.cwl.workflow import (
    Task,
    Input,
    Output,
    Workflow,
    MPI,
    Slurm,
    Script,
    TaskReq,
)
from beeflow.common.object_models import Hint
from beeflow.common.parser import BeeParseError, BeeParser
from beeflow.common.workflow_api import Resources


def cat_grep_tar_spec():
    """Build the cat-grep-tar workflow with the python workflow API."""
    cat = Task(
        name="cat",
        base_command="cat",
        stdout="cat.txt",
        stderr="cat.err",
        inputs=[Input("input_file", "File", "lorem.txt", position=1)],
        outputs=[
            Output("contents", "stdout"),
            Output("cat_stderr", "stderr", source="cat/cat_stderr"),
        ],
    )
    grep0 = Task(
        name="grep0",
        base_command="grep",
        stdout="occur0.txt",
        inputs=[
            Input("word0", "string", "Vivamus", position=1),
            Input("text_file", "File", "cat/contents", position=2),
        ],
        outputs=[Output("occur", "stdout")],
    )
    grep1 = Task(
        name="grep1",
        base_command="grep",
        stdout="occur1.txt",
        inputs=[
            Input("word1", "string", "pulvinar", position=1),
            Input("text_file", "File", "cat/contents", position=2),
        ],
        outputs=[Output("occur", "stdout")],
    )
    tar = Task(
        name="tar",
        base_command="tar",
        stdout="occur1.txt",
        inputs=[
            Input("tarball_fname", "string", "out.tgz", position=1, prefix="-cf"),
            Input("file0", "File", "grep0/occur", position=2),
            Input("file1", "File", "grep1/occur", position=3),
        ],
        outputs=[
            Output("tarball", "File", glob="out.tgz", source="tar/tarball")
        ],
    )
    return Workflow("cat-grep-tar", [cat, grep0, grep1, tar])


def test_parse_workflow_object(tmp_path):
    """Test parsing an in-memory python workflow specification."""
    workflow, tasks = BeeParser().parse_workflow(
        "abc123", "cat-grep-tar", cat_grep_tar_spec(), workdir=str(tmp_path)
    )
    assert workflow.id == "abc123"
    assert workflow.name == "cat-grep-tar"
    # Workflow inputs are the literal-valued (non-sourced) task inputs
    assert [(input_.id, input_.type, input_.value) for input_ in workflow.inputs] == [
        ("input_file", "File", "lorem.txt"),
        ("word0", "string", "Vivamus"),
        ("word1", "string", "pulvinar"),
        ("tarball_fname", "string", "out.tgz"),
    ]
    # Workflow outputs are the sourced task outputs
    assert [(output.id, output.type, output.source) for output in workflow.outputs] == [
        ("cat_stderr", "File", "cat/cat_stderr"),
        ("tarball", "File", "tar/tarball"),
    ]
    assert [task.name for task in tasks] == ["cat", "grep0", "grep1", "tar"]


def test_parse_task_inputs_and_outputs(tmp_path):
    """Test the conversion of task inputs and outputs."""
    _, tasks = BeeParser().parse_workflow(
        "abc123", "cat-grep-tar", cat_grep_tar_spec(), workdir=str(tmp_path)
    )
    cat = tasks[0]
    assert cat.base_command == "cat"
    assert cat.stdout == "cat.txt"
    assert cat.stderr == "cat.err"
    assert cat.workflow_id == "abc123"

    # A literal-valued input references a workflow input of the same name and
    # carries the spec value as its default
    (input_file,) = cat.inputs
    assert input_file.id == "input_file"
    assert input_file.type == "File"
    assert input_file.value is None
    assert input_file.default == "lorem.txt"
    assert input_file.source == "input_file"
    assert input_file.position == 1

    # stdout/stderr outputs capture the corresponding file
    contents, cat_stderr = cat.outputs
    assert contents.id == "cat/contents"
    assert contents.type == "stdout"
    assert contents.glob == str(tmp_path / "cat.txt")
    assert cat_stderr.id == "cat/cat_stderr"
    assert cat_stderr.type == "stderr"
    assert cat_stderr.glob == str(tmp_path / "cat.err")

    # A sourced input depends on another task's output
    grep0 = tasks[1]
    word0, text_file = grep0.inputs
    assert word0.source == "word0"
    assert text_file.source == "cat/contents"
    assert text_file.default is None


def test_parse_task_outputs_no_glob_adds_workdir(tmp_path):
    """Test that relative output globs are resolved against the workdir."""
    task = Task(
        name="copy",
        base_command="cp",
        inputs=[],
        outputs=[Output("outfile", "File", glob="out.txt")],
    )
    spec = Workflow("copy-wf", [task])
    _, tasks = BeeParser().parse_workflow(
        "def456", "copy-wf", spec, workdir=str(tmp_path)
    )
    (output,) = tasks[0].outputs
    assert output.id == "copy/outfile"
    assert output.glob == str(tmp_path / "out.txt")


def test_parse_task_hints(tmp_path, monkeypatch):
    """Test conversion of python API hints into Hint objects."""
    (tmp_path / "comd_pre.sh").write_text("#!/bin/bash\necho starting\n")
    monkeypatch.chdir(tmp_path)
    task = Task(
        name="comd",
        base_command="comd",
        inputs=[],
        outputs=[],
        hints=[
            MPI(nodes=4, ntasks=8),
            Slurm(time_limit=500, account="standard"),
            Script(pre_script="comd_pre.sh", shell="/bin/bash"),
        ],
    )
    spec = Workflow("comd", [task])
    _, tasks = BeeParser().parse_workflow(
        "abc123", "comd", spec, workdir=str(tmp_path)
    )
    hints = tasks[0].hints
    assert Hint(class_="beeflow:MPIRequirement", params={"nodes": 4, "ntasks": 8}) in hints
    assert Hint(
        class_="beeflow:SlurmRequirement",
        params={"timeLimit": 500, "account": "standard"},
    ) in hints
    # The pre_script file contents are read in at parse time and the shebang
    # line is validated against the shell and stripped
    script_hint = next(h for h in hints if h.class_ == "beeflow:ScriptRequirement")
    assert script_hint.params["pre_script"] == "echo starting"
    assert script_hint.params["shell"] == "/bin/bash"


def test_parse_task_requirement_workdir(tmp_path):
    """Test that a TaskReq hint sets the task workdir."""
    task = Task(
        name="special",
        base_command="true",
        inputs=[],
        outputs=[],
        hints=[TaskReq(workdir="special_dir")],
    )
    spec = Workflow("workdir-wf", [task])
    _, tasks = BeeParser().parse_workflow(
        "abc123", "workdir-wf", spec, workdir=str(tmp_path)
    )
    assert tasks[0].workdir == str(tmp_path / "special_dir")


def test_parse_workflow_job_file(tmp_path):
    """Test that the job file overrides the literal spec values."""
    job = tmp_path / "job.yaml"
    job.write_text("input_file: other.txt\nword0: Curabitur\n")
    workflow, _ = BeeParser().parse_workflow(
        "abc123", "cat-grep-tar", cat_grep_tar_spec(), job=str(job)
    )
    values = {input_.id: input_.value for input_ in workflow.inputs}
    assert values["input_file"] == "other.txt"
    assert values["word0"] == "Curabitur"
    # Inputs absent from the job file keep their spec values
    assert values["word1"] == "pulvinar"
    assert values["tarball_fname"] == "out.tgz"


def test_parse_workflow_from_file(tmp_path):
    """Test parsing a .py workflow specification file."""
    spec_file = tmp_path / "hello_workflow.py"
    spec_file.write_text(
        textwrap.dedent(
            """
            from beeflow.common.cwl.workflow import Task, Input, Output, Workflow

            workflow = Workflow(
                "hello",
                [
                    Task(
                        name="hello",
                        base_command="echo",
                        stdout="out.txt",
                        inputs=[Input("msg", "string", "hello world", position=1)],
                        outputs=[Output("out", "stdout")],
                    )
                ],
            )
            """
        )
    )
    workflow, tasks = BeeParser().parse_workflow(
        "abc123", None, str(spec_file), workdir=str(tmp_path)
    )
    # Falls back to the name from the specification
    assert workflow.name == "hello"
    assert workflow.main_cwl == str(spec_file.resolve())
    assert [task.name for task in tasks] == ["hello"]
    assert tasks[0].inputs[0].default == "hello world"


def test_parse_workflow_from_file_main(tmp_path):
    """Test that a spec file returning a workflow from main() is supported."""
    spec_file = tmp_path / "hello_main.py"
    spec_file.write_text(
        textwrap.dedent(
            """
            from beeflow.common.cwl.workflow import Task, Workflow

            def main():
                task = Task(name="hello", base_command="echo", outputs=[])
                return Workflow("hello", [task])

            if __name__ == "__main__":
                main()
            """
        )
    )
    workflow, tasks = BeeParser().parse_workflow(
        "abc123", "hello", str(spec_file), workdir=str(tmp_path)
    )
    assert workflow.name == "hello"
    assert [task.name for task in tasks] == ["hello"]


def test_parse_workflow_missing_input():
    """Test that an input without a value raises a parse error."""
    task = Task(
        name="cat",
        base_command="cat",
        inputs=[Input("input_file", "File")],
        outputs=[],
    )
    spec = Workflow("missing-input", [task])
    with pytest.raises(BeeParseError, match="input_file is missing"):
        BeeParser().parse_workflow("abc123", "missing-input", spec)


def test_parse_workflow_missing_spec():
    """Test that a nonexistent spec file raises a parse error."""
    with pytest.raises(BeeParseError, match="not found"):
        BeeParser().parse_workflow("abc123", "test", "nonexistent_workflow.py")


def test_parse_workflow_invalid_job_file(tmp_path):
    """Test that an unsupported job file extension raises a parse error."""
    job = tmp_path / "job.txt"
    job.write_text("input_file: lorem.txt\n")
    with pytest.raises(BeeParseError, match="Unsupported input job file extension"):
        BeeParser().parse_workflow(
            "abc123", "cat-grep-tar", cat_grep_tar_spec(), job=str(job)
        )


def bee_cat_grep_tar_spec():
    """Build the cat-grep-tar workflow with the new python workflow API."""
    workflow = workflow_api.Workflow(
        name="cat-grep-tar",
        description="Cat an input file, grep it two ways, and tar the results",
    )
    cat = workflow.add_task(
        name="cat",
        commands=["cat {input_file}"],
        inputs={"input_file": "lorem.txt"},
        stdout="cat.txt",
        stderr="cat.err",
        outputs={"contents": "cat.txt", "cat_stderr": "cat.err"},
    )
    grep0 = workflow.add_task(
        name="grep0",
        commands=["grep {word0} {text_file}"],
        params={"word0": "Vivamus"},
        inputs={"text_file": cat.output("contents")},
        stdout="occur0.txt",
        outputs={"occur": "occur0.txt"},
    )
    grep1 = workflow.add_task(
        name="grep1",
        commands=["grep {word1} {text_file}"],
        params={"word1": "pulvinar"},
        inputs={"text_file": cat.output("contents")},
        stdout="occur1.txt",
        outputs={"occur": "occur1.txt"},
    )
    workflow.add_task(
        name="tar",
        commands=["tar -cf {tarball_fname} {file0} {file1}"],
        inputs={
            "tarball_fname": "out.tgz",
            "file0": grep0.output("occur"),
            "file1": grep1.output("occur"),
        },
        resources=Resources(nodes=1, ntasks=2, walltime="01:00:00"),
        scheduler_options={"account": "standard", "partition": "standard"},
        outputs={"tarball": "out.tgz"},
    )
    return workflow


def test_parse_bee_api_workflow(tmp_path):
    """Test parsing a workflow built with the new python workflow API."""
    workflow, tasks = BeeParser().parse_workflow(
        "bee123", "cat-grep-tar", bee_cat_grep_tar_spec(), workdir=str(tmp_path)
    )
    assert workflow.id == "bee123"
    assert workflow.name == "cat-grep-tar"
    assert [(input_.id, input_.value) for input_ in workflow.inputs] == [
        ("input_file", "lorem.txt"),
        ("word0", "Vivamus"),
        ("word1", "pulvinar"),
        ("tarball_fname", "out.tgz"),
    ]
    assert [output.id for output in workflow.outputs] == [
        "cat/contents",
        "cat/cat_stderr",
        "grep0/occur",
        "grep1/occur",
        "tar/tarball",
    ]
    assert [task.name for task in tasks] == ["cat", "grep0", "grep1", "tar"]


def test_parse_bee_api_task_conversion(tmp_path):
    """Test the conversion of new API task inputs, outputs, and commands."""
    _, tasks = BeeParser().parse_workflow(
        "bee123", "cat-grep-tar", bee_cat_grep_tar_spec(), workdir=str(tmp_path)
    )
    cat, grep0, _, tar = tasks

    # {name} placeholders stay in the command tokens for runtime substitution
    assert cat.base_command == ["cat", "{input_file}"]
    assert grep0.base_command == ["grep", "{word0}", "{text_file}"]

    # Static values become workflow-input-backed defaults
    input_file = cat.inputs[0]
    assert input_file.id == "input_file"
    assert input_file.source == "input_file"
    assert input_file.default == "lorem.txt"
    assert input_file.value is None

    # task.output() references become dependencies on the producer's output
    text_file = grep0.inputs[1]
    assert text_file.id == "text_file"
    assert text_file.source == "cat/contents"
    assert text_file.default is None

    # Outputs collect the named files, resolved against the workdir
    assert [output.id for output in cat.outputs] == [
        "cat/contents",
        "cat/cat_stderr",
    ]
    assert cat.outputs[0].glob == str(tmp_path / "cat.txt")
    assert cat.outputs[0].type == "File"
    assert tar.outputs[0].glob == str(tmp_path / "out.tgz")


def test_bee_api_command_placeholders_filled(tmp_path):
    """Test that {name} placeholders are filled from the input values."""
    _, tasks = BeeParser().parse_workflow(
        "bee123", "cat-grep-tar", bee_cat_grep_tar_spec(), workdir=str(tmp_path)
    )
    grep0 = tasks[1]
    # Simulate the graph database filling in the input values
    for input_ in grep0.inputs:
        input_.value = "Vivamus" if input_.id == "word0" else "cat.txt"
    assert grep0.command == ["grep", "Vivamus", "cat.txt"]

    # A missing placeholder value raises an error
    grep0.inputs[1].value = None
    with pytest.raises(ValueError, match="missing placeholder value"):
        _ = grep0.command


def test_bee_api_resources_and_scripts(tmp_path, monkeypatch):
    """Test resources, scheduler options, and pre/post scripts as hints."""
    (tmp_path / "run_pre.sh").write_text("#!/bin/bash\necho start\n")
    (tmp_path / "run_post.sh").write_text("#!/bin/bash\necho done\n")
    monkeypatch.chdir(tmp_path)
    task = workflow_api.Task(
        name="comd",
        commands=["/CoMD/bin/CoMD-mpi -e"],
        resources=Resources(
            nodes=4, ntasks=8, tasks_per_node=2, walltime="02:00:00"
        ),
        scheduler_options={"account": "standard", "qos": "debug"},
        pre_script="run_pre.sh",
        post_script="run_post.sh",
        outputs={},
    )
    spec = workflow_api.Workflow("comd", tasks=[task])
    _, tasks = BeeParser().parse_workflow(
        "bee123", "comd", spec, workdir=str(tmp_path)
    )
    hints = tasks[0].hints
    assert Hint(
        class_="beeflow:MPIRequirement",
        params={"nodes": 4, "ntasks": 8, "tasks_per_node": 2},
    ) in hints
    assert Hint(
        class_="beeflow:SlurmRequirement",
        params={"timeLimit": "02:00:00", "account": "standard", "qos": "debug"},
    ) in hints
    script_hint = next(h for h in hints if h.class_ == "beeflow:ScriptRequirement")
    assert script_hint.params["pre_script"] == "echo start"
    assert script_hint.params["post_script"] == "echo done"


def test_bee_api_job_file_overrides_params(tmp_path):
    """Test that the job file overrides new API params and inputs."""
    job = tmp_path / "job.yaml"
    job.write_text("input_file: other.txt\n")
    workflow, _ = BeeParser().parse_workflow(
        "bee123", "cat-grep-tar", bee_cat_grep_tar_spec(), job=str(job)
    )
    values = {input_.id: input_.value for input_ in workflow.inputs}
    assert values["input_file"] == "other.txt"
    assert values["word0"] == "Vivamus"


def test_bee_api_conflicting_params_stay_task_local(tmp_path):
    """Test that same-named params with different values stay task-local."""
    workflow = workflow_api.Workflow("conflict")
    workflow.add_task(
        name="grep0",
        commands=["grep {word} {file}"],
        params={"word": "Vivamus"},
        inputs={"file": "in.txt"},
        outputs={},
    )
    workflow.add_task(
        name="grep1",
        commands=["grep {word} {file}"],
        params={"word": "pulvinar"},
        inputs={"file": "in.txt"},
        outputs={},
    )
    wf, tasks = BeeParser().parse_workflow(
        "bee123", "conflict", workflow, workdir=str(tmp_path)
    )
    # 'word' is task-local (conflicting values), 'file' is a workflow input
    assert [input_.id for input_ in wf.inputs] == ["file"]
    grep0_word = tasks[0].inputs[0]
    assert grep0_word.id == "word"
    assert grep0_word.default == "Vivamus"


def test_bee_api_undeclared_placeholder():
    """Test that a command placeholder without a declared value errors."""
    workflow = workflow_api.Workflow("bad")
    workflow.add_task(name="bad", commands=["echo {missing}"], outputs={})
    with pytest.raises(BeeParseError, match=r"references \{missing\}"):
        BeeParser().parse_workflow("bee123", "bad", workflow)


def test_bee_api_dependson_without_data():
    """Test that a non-data depends_on dependency raises an error."""
    workflow = workflow_api.Workflow("deps")
    setup = workflow.add_task(name="setup", commands=["echo setup"], outputs={})
    workflow.add_task(
        name="run",
        commands=["echo run"],
        outputs={},
        depends_on=[setup],
    )
    with pytest.raises(BeeParseError, match="without sharing any data"):
        BeeParser().parse_workflow("bee123", "deps", workflow)


def test_bee_api_add_task_and_output_refs():
    """Test add_task() forms and output() references."""
    workflow = workflow_api.Workflow("add-task")
    task = workflow_api.Task(name="t0", commands=["echo hi"], outputs={"out": "o.txt"})
    assert workflow.add_task(task) is task
    created = workflow.add_task(name="t1", commands=["echo bye"], outputs={})
    assert created.name == "t1"
    assert workflow.tasks == [task, created]

    # task.output() returns a qualified reference
    ref = task.output("out")
    assert str(ref) == "t0/out"
    with pytest.raises(workflow_api.WorkflowAPIError, match="no output"):
        task.output("missing")

    with pytest.raises(workflow_api.WorkflowAPIError):
        workflow.add_task()
    with pytest.raises(workflow_api.WorkflowAPIError):
        workflow.add_task("not a task")


def test_parse_bee_api_from_file(tmp_path):
    """Test parsing a new API specification from a .py file."""
    spec_file = tmp_path / "hello_bee.py"
    spec_file.write_text(
        textwrap.dedent(
            """
            from beeflow.common.workflow_api import Workflow

            workflow = Workflow(name="hello")
            workflow.add_task(
                name="hello",
                commands=["echo {msg}"],
                params={"msg": "hello world"},
                stdout="out.txt",
                outputs={"out": "out.txt"},
            )
            """
        )
    )
    workflow, tasks = BeeParser().parse_workflow(
        "bee123", None, str(spec_file), workdir=str(tmp_path)
    )
    assert workflow.name == "hello"
    assert workflow.main_cwl == str(spec_file.resolve())
    assert tasks[0].base_command == ["echo", "{msg}"]
    assert tasks[0].inputs[0].default == "hello world"
