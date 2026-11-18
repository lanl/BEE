# CWL Migration Plan

This document describes the plan for pivoting BEE away from CWL toward a
Python workflow description API with an equivalent YAML front end, and how to
use and test the new API on this branch. The motivation and design sketches come from the
migration documents in `docs/todo/` and are tracked in
[issue #1194](https://github.com/lanl/BEE/issues/1194).

With the new API, a workflow is written as a python module that builds a
`Workflow` object (containing `Task` objects) using the classes in
`beeflow.common.workflow_api`. The `BeeParser`
(`beeflow/common/parser/parser.py`) converts that specification directly into
the `Workflow` and `Task` objects loaded into the graph database by the
`WorkflowInterface` — no CWL is generated or parsed.

## Migration plan

The work is split into four phases. Phases 1–3 are implemented on this branch;
phase 4 is in progress, with restart fixes and the optional format-adapter boundary implemented.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | New python API (`workflow_api.py`), `BeeParser` conversion, runtime `{placeholder}` command substitution, simplified `beeflow submit` (workflow path only) | Complete |
| 2 | Explicit `depends_on` dependencies that don't share data (graph database dependency edges); task workdirs and containers; multiple commands per task | Implemented on this branch; validation in progress |
| 3 | Versioned YAML front end translating to the Python API; single-file/directory/archive submission, examples and authoring reference | Implemented on this branch; local validation in progress |
| 4 | Isolate optional CWL support behind workflow-format adapters; clean up core models, add conversion and update examples/tests/docs (issues #1197-#1205) | Restart fixes and adapters implemented; model cleanup and converter pending |

The CWL parser and the older `beeflow.common.cwl.workflow` API remain supported
with optional CWL dependencies installed, so both can be compared while the pivot progresses.

## Phase 4 compatibility direction

The revised goal is a CWL-independent core, **not** dropping existing CWL
submissions. The scoped READY gate remains the selected behavior: only explicit
`depends_on` edges add a terminal-predecessor check; data-only edges retain
input-based readiness. Slurm/Flux testing on HPC is deferred until phase 4 is
complete so the combined final state can be validated there.

The first phase-4 fix transfers restart dependency edges by old/new task IDs,
preserving explicit flags and current upstream attempt IDs even when the workflow
interface renames replacements. Re-inferring from task names could lose explicit
edges or restore links to obsolete attempts. SQLite rewiring uses one transaction;
Neo4j rewiring stays within the driver's write transaction. Regression coverage
goes through WorkflowInterface, including repeated restarts, mixed edges,
upstream restarts, forward loading and task names containing numeric suffixes.

The format-adapter boundary is now implemented; see the
[adapter reference](sphinx/workflow_formats.rst) for the contract and extension example.

- Built-in Python/YAML readers and optional CWL parsing share a workflow-format
  registry for discovery, submission, archives, reexecution and the parser CLI.
- CWL imports are lazy. Install compatibility dependencies with
  `pip install 'hpc-beeflow[cwl]'` (or `poetry install --extras cwl` in a checkout).
  The core-only runtime can parse Python/YAML without CWL packages installed.
- Installed extensions register readers through the `beeflow.workflow_formats`
  entry point group. Adapters return common execution models and can request
  parent-directory bundling for linked resources. Discovery does not parse or
  execute workflow code. Broken/conflicting extensions are reported explicitly.

Remaining phase-4 work:

- Preserve reading existing workflow metadata/archives where practical; keep
  existing CWL execution available through its adapter. Unsupported constructs
  must be reported, not silently converted with changed semantics.
- A conversion command should infer the output format from `--output`, with
  optional `--to` overriding inference. A mismatch warns; an unknown suffix
  without `--to` errors. Existing output files require an explicit overwrite
  option. Adapters advertise writing support separately from reading support.
  No conversion CLI is implemented in the current adapter slice.
- Audit feature parity (checkpoint settings, builders and scheduler options)
  before removing any legacy definitions or runtime models. Internal hint and
  requirement objects still consumed by workers are not automatically obsolete
  merely because their names originated in CWL.

## YAML front end and authoring reference

See [`docs/sphinx/workflow_spec.rst`](sphinx/workflow_spec.rst) for the complete
Python/YAML tutorial, field reference, path rules and submission options.
The [testing guide](sphinx/workflow_testing.rst) covers parser/regression tests
and reproducible live BEE submission using an isolated Linux Docker instance.
YAML is an alternative to a Python specification, not an extra required file:

```sh
beeflow submit examples/yaml-workflow/workflow.yaml
python -m beeflow.common.parser examples/yaml-workflow/workflow.yaml
```

One workflow file is sufficient when its external resources are accessible;
a separate `--job` override file is optional. A minimal YAML workflow is:

```yaml
bee_version: 1
tasks:
  hello:
    commands: echo Hello from BEE
```

Tasks are named mapping entries. Output references use `{from: task/output}`;
`depends_on` lists task names. The loader resolves forward references and builds
Python API objects, then delegates to the same semantic validation/conversion
as Python workflows. Duplicate keys, unknown fields and unsupported versions
are errors. Safe loading never executes Python tags.

Directory/archive discovery identifies YAML workflows by `bee_version`, excludes
them from job-input candidates, and reports ambiguous Python/YAML selections.
The existing `--main-cwl` option can explicitly select the main file during
migration. Python/YAML workflow candidates are preferred over legacy CWL files.

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
  that name. A task may provide multiple command strings; BEE runs them in
  order using `&&`, so a command runs only when the preceding command
  succeeds.
- **`params` vs `inputs`**: `params` holds task-local values; `inputs` holds
  task inputs, which can be static values or `task.output("name")` references
  (which create dependencies automatically). A name declared with the same
  value in every task becomes a *workflow input* — overridable through the
  job file — while names declared with conflicting values stay task-local.
- **Outputs** collect the named files; every task output is exposed as a
  workflow output as well.
- **`depends_on`** declares tasks that must reach a final state before this
  task becomes ready, even when no data is shared. Output references also
  create data-flow dependencies automatically.
- **Workdirs and containers**: `workdir=` selects a task working directory
  relative to the workflow workdir. `container=` accepts an image string or
  a `Container` with bind mounts and an optional hard requirement.
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
python3 -m beeflow.common.parser workflow.py [-i job.yaml]
```

The optional job file (YAML or JSON) provides workflow input values that
override the values in the specification:

```yaml
# job.yaml
input_file: other.txt
word: Curabitur
```

### Submitting a job to BEE

`beeflow submit` now takes the python specification directly and derives
everything else from it: the workflow name, the working directory, and the
job inputs. With BEE core running (`beeflow core start`):

```sh
beeflow submit examples/cat-grep-tar/workflow.py
beeflow query <wf_id>
```

The working directory is created automatically under
`~/.beeflow/workflows/<name>` (or `./bee-workflows/<name>` when `~/.beeflow`
does not exist), and the workflow input values come from the specification
itself. A job input file can still be supplied to override the spec values
with `--job`, for example `examples/cat-grep-tar/input.yml`:

```yaml
input_file: lorem.txt
word0: Vivamus
word1: pulvinar
tarball_fname: out.tgz
```

The remaining options (`--name`, `--workdir`, `--main-cwl`, and
`--no-start`) override the derived defaults; as before, the working directory
cannot be in `/tmp` or `/var/tmp`. The old multi-argument form
(`beeflow submit WF_NAME WF_PATH MAIN_CWL YAML WORKDIR`) was removed in
favor of the single-path form; a compatibility shim can be added back if
existing scripts need it.

## Testing it

Run the cat-grep-tar example and inspect the parsed workflow and tasks:

```sh
cd examples/cat-grep-tar
python3 workflow.py
```

Parse the same example from its file with the job file:

```sh
cd examples/cat-grep-tar
python3 -m beeflow.common.parser workflow.py -i input.yml
```

Run the unit tests for the new parser (and the existing CWL parser, to
confirm the CWL path is unaffected):

```sh
pytest beeflow/tests/test_bee_parser.py beeflow/tests/test_parser.py
```

Live Neo4j regression checks are opt-in. They use a separate, disposable
authentication-disabled Neo4j 5 instance and roll back all test writes. For
example, with Docker available:

```sh
docker run -d --name bee-phase2-neo4j-check \
  -p 127.0.0.1:17687:7687 -e NEO4J_AUTH=none neo4j:5-community
# Wait for Neo4j to finish starting before running the tests.
BEE_TEST_NEO4J_URI=bolt://127.0.0.1:17687 \
  pytest beeflow/tests/test_phase2_neo4j.py -q
docker stop bee-phase2-neo4j-check
docker rm -v bee-phase2-neo4j-check
```

Without `BEE_TEST_NEO4J_URI`, these tests are skipped. The checks cover tasks
with no input nodes, explicit-edge gating in either load order, terminal-state
release, restart edge remapping, and command storage. Neo4j cannot store nested
lists as node properties, so multi-command tasks use a JSON string property;
legacy string and flat-list command properties remain readable unchanged.

The local worker tests exercise ordered execution through the Python parser,
SQLite storage and SimpleWorker, task workdirs, failed-command short-circuiting,
and checkpoint argument placement. These do not replace live scheduler and
container-image execution on a supported Linux environment.

## Status and limitations

Phases 1–3 are implemented on this branch. Remaining migration work:

- YAML front-end integration needs review and supported-environment validation;
  it does not change runtime execution semantics.
- Explicit dependency readiness has live Neo4j regression coverage and local
  SQLite/worker coverage. Full service orchestration, scheduler execution and
  task execution inside container images still need Linux/HPC validation.
- Workflow-level (rather than task-level) hints/requirements and additional
  metadata (author, tags) are deferred to later discussions.
- The `Workflow`/`Task` pydantic models still carry CWL fields such as
  `main_cwl` (currently set to the `.py` spec path); cleaning these up is
  phase 4 (issue #1204).
- The CWL parser, `dump_wf()` CWL generation, and CWL-based submit path all
  continue to work unchanged.
