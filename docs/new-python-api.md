# New Python Workflow API

This document describes the new BEE python workflow description API and its
parser. This work is part of the pivot away from CWL tracked in
[issue #1194](https://github.com/lanl/BEE/issues/1194) and is exploratory: the
CWL parser remains fully supported.

With the new API, a workflow is written as a python module that builds a
`Workflow` object (containing `Task` objects) using the classes in
`beeflow.common.cwl.workflow`. The `BeeParser`
(`beeflow/common/parser/parser.py`) converts that specification directly into
the `Workflow` and `Task` objects loaded into the graph database by the
`WorkflowInterface` — no CWL is generated or parsed.

## Development environment setup

Use a python virtual environment with Poetry for dependency installation
(see `AGENTS.md` for details):

```sh
python3 -m venv beedev-env
source beedev-env/bin/activate
pip install poetry
cd <path to BEE repo>
poetry install
```

## Writing a workflow

A workflow specification is a python module that assigns a `Workflow` object
to a module-level `workflow` variable (a `main()` or `build()` function
returning one also works). A simple two-task example:

```python
"""My workflow, written with the BEE python API."""
from beeflow.common.cwl.workflow import Task, Input, Output, Workflow, MPI

# 'cat' copies the input file to stdout (captured in cat.txt)
cat = Task(
    name="cat",
    base_command="cat",
    stdout="cat.txt",
    # A literal value becomes a workflow input of the same name.
    # The value from the job file (if given) overrides it.
    inputs=[Input("input_file", "File", "lorem.txt", position=1)],
    outputs=[Output("contents", "stdout")],
)

# 'grep' searches the cat output for a word
grep = Task(
    name="grep",
    base_command="grep",
    stdout="occur.txt",
    inputs=[
        Input("word", "string", "Vivamus", position=1),
        # An Input value of the form "task/output" depends on another
        # task's output; the graph database creates the dependency
        # automatically.
        Input("text_file", "File", "cat/contents", position=2),
    ],
    # A source makes the output visible as a workflow output
    outputs=[Output("occur", "stdout", source="grep/occur")],
    # Hints use the same requirement classes as before (MPI, Slurm,
    # Charliecloud, Script, Checkpoint, TaskReq, Workload)
    hints=[MPI(nodes=2, ntasks=4)],
)

workflow = Workflow("cat-grep", [cat, grep])
```

Key points:

- **Task inputs**: a literal value (e.g. `"lorem.txt"`) becomes a *workflow
  input*; a value of the form `"task/output"` (e.g. `"prep/copy"`) becomes a
  dependency on that task's output.
- **Task outputs**: `Output(name, run_type)` where `run_type` is `"stdout"`,
  `"stderr"`, or a type such as `"File"`. Setting `source="task/output"`
  exposes the output at the workflow level; `glob` names the output file for
  non-stream outputs.
- **Hints** are converted using the existing requirement classes, so the
  parameter names seen by the rest of BEE are unchanged.

See `examples/cat-grep-tar/workflow.py` for a complete worked example that
recreates the `workflow.cwl` version found in the same directory.

## Using the parser

There are three ways to use a workflow specification.

### As a module

```python
from beeflow.common.parser import BeeParser

parser = BeeParser()
# spec can be a Workflow object or the path of a .py specification file
workflow, tasks = parser.parse_workflow(workflow_id, workflow_name, spec)
```

The returned objects can be loaded directly into the workflow interface:

```python
from beeflow.common.wf_interface import WorkflowInterface

wfi = WorkflowInterface(workflow.id)
wfi.initialize_workflow(workflow)
for task in tasks:
    wfi.add_task(task)
```

### From the command line

Parse a specification and print the resulting workflow and tasks:

```sh
python3 -m beeflow.common.parser.parser workflow.py [-i job.yaml]
```

The optional job file (YAML or JSON) provides workflow input values that
override the literal values in the specification:

```yaml
# job.yaml
input_file: other.txt
word: Curabitur
```

### Submitting a job to BEE

`beeflow submit` accepts a python specification in place of the main CWL
file. With BEE core running (`beeflow core start`):

```sh
beeflow submit cat-grep-tar . workflow.py input.yml <workdir>
beeflow query <wf_id>
```

where `input.yml` supplies the workflow input values, for example
`examples/cat-grep-tar/input.yml`:

```yaml
input_file: lorem.txt
word0: Vivamus
word1: pulvinar
tarball_fname: out.tgz
```

As with CWL workflows, `<workdir>` must already exist and cannot be in `/tmp`
or `/var/tmp`.

## Testing it

Run the cat-grep-tar example and inspect the parsed workflow and tasks:

```sh
cd examples/cat-grep-tar
python3 workflow.py
```

Parse the same example from its file with the job file:

```sh
cd examples/cat-grep-tar
python3 -m beeflow.common.parser.parser workflow.py -i input.yml
```

Run the unit tests for the new parser (and the existing CWL parser, to
confirm the CWL path is unaffected):

```sh
pytest beeflow/tests/test_bee_parser.py beeflow/tests/test_parser.py
```

## Status and limitations

This branch is an early exploration of the pivot; the following are not yet
supported or handled differently from the eventual design:

- Only *task-level* hints are part of the specification; workflow-level
  hints/requirements and scattered features (e.g. workflow-level MPI)
  still need a place in the API (issue #1197).
- The `Workflow`/`Task` pydantic models and `WF_Interface` still carry CWL
  fields such as `main_cwl` (currently set to the `.py` spec path).
- The CWL parser, `dump_wf()` CWL generation, and CWL-based submit path all
  continue to work unchanged.
- Remaining follow-on work is tracked by the sub-issues of
  [issue #1194](https://github.com/lanl/BEE/issues/1194) (examples/CI #1198,
  tests #1199-#1201, docs #1202, pydantic models #1204, submit #1205).
