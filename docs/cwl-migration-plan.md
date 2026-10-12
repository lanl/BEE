# CWL Migration Plan

This document describes the plan for pivoting BEE away from CWL toward a
purely python-based workflow description API, and how to use and test the new
API on this branch. The motivation and design sketches come from the
migration documents in `docs/todo/` and are tracked in
[issue #1194](https://github.com/lanl/BEE/issues/1194).

With the new API, a workflow is written as a python module that builds a
`Workflow` object (containing `Task` objects) using the classes in
`beeflow.common.workflow_api`. The `BeeParser`
(`beeflow/common/parser/parser.py`) converts that specification directly into
the `Workflow` and `Task` objects loaded into the graph database by the
`WorkflowInterface` — no CWL is generated or parsed.

## Migration plan

The work is split into four phases. Phase 1 is implemented on this branch;
the remaining phases are exploratory designs.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | New python API (`workflow_api.py`), `BeeParser` conversion, runtime `{placeholder}` command substitution, `beeflow submit` accepting `.py` specs | This branch |
| 2 | Explicit `depends_on` dependencies that don't share data (graph database dependency edges); task workdirs and containers in the new API | Not started |
| 3 | YAML front end describing the same schema (see the YAML slides in `docs/todo/`) | Not started |
| 4 | Remove CWL: delete `cwl.py`/`dump_wf`, the CWL parser path, and CWL-specific pydantic fields; update examples, CI, and docs (issues #1197-#1205) | Not started |

The CWL parser and the older `beeflow.common.cwl.workflow` API continue to
work unchanged, so both can be compared while the pivot progresses.

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
from beeflow.common.workflow_api import Workflow, Resources

workflow = Workflow(
    name="cat-grep",
    description="Cat a file then grep the output",
)

cat = workflow.add_task(
    name="cat",
    # {name} placeholders are filled in at execution time from the task's
    # params and inputs
    commands=["cat {input_file}"],
    inputs={"input_file": "lorem.txt"},
    stdout="cat.txt",
    # outputs map output names to the files they collect
    outputs={"contents": "cat.txt"},
)

workflow.add_task(
    name="grep",
    commands=["grep {word} {text_file}"],
    params={"word": "Vivamus"},
    # task.output("name") depends on another task's output
    inputs={"text_file": cat.output("contents")},
    stdout="occur.txt",
    # resources and scheduler_options replace the old MPI/Slurm hints
    resources=Resources(nodes=2, ntasks=4, walltime="01:00:00"),
    scheduler_options={"account": "standard", "partition": "standard"},
    outputs={"occur": "occur.txt"},
)
```

Key points:

- **Commands and placeholders**: a `{name}` placeholder in a command is
  replaced at execution time by the value of the task's param or input of
  that name.
- **`params` vs `inputs`**: `params` holds task-local values; `inputs` holds
  task inputs, which can be static values or `task.output("name")` references
  (which create dependencies automatically). A name declared with the same
  value in every task becomes a *workflow input* — overridable through the
  job file — while names declared with conflicting values stay task-local.
- **Outputs** collect the named files; every task output is exposed as a
  workflow output as well.
- **`depends_on`** may be used to document dependencies; in this first phase
  each dependency must also be implied by an input/output reference, since
  the graph database still infers edges from data flow.
- **Scripts**: `pre_script`/`post_script` name script files (whose shebang
  line must match `/bin/bash`) that run before/after the command.

See `examples/cat-grep-tar/workflow.py` for a complete worked example that
recreates the same workflow as the `workflow.cwl` version in that directory.

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
override the values in the specification:

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

Phase 1 of the migration is complete on this branch, with the following
known limitations:

- Each task supports a **single command**; multiple commands per task (as in
  the design sketches) are not yet supported.
- `depends_on` entries must be implied by data flow (an input referencing
  `task.output(...)`); non-data dependencies are rejected with a clear error
  until phase 2 adds graph database support for explicit dependency edges.
- Containers (Charliecloud/Docker) and per-task workdirs have no equivalent
  in the new API yet; those remain available through the old API's hints.
- Workflow-level (rather than task-level) hints/requirements and additional
  metadata (author, tags) are deferred to later discussions.
- The `Workflow`/`Task` pydantic models still carry CWL fields such as
  `main_cwl` (currently set to the `.py` spec path); cleaning these up is
  phase 4 (issue #1204).
- The CWL parser, `dump_wf()` CWL generation, and CWL-based submit path all
  continue to work unchanged.
