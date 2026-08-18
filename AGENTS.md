# AGENTS.md

Guidance for AI coding agents (and humans) working in the **BEE** repository.

## Project Overview

**BEE (Build and Execution Environment)** is a workflow orchestration system that
builds containerized HPC applications and orchestrates workflows across HPC and
cloud systems. Workflows are specified in the [Common Workflow Language
(CWL)](https://www.commonwl.org/), managed/visualized through a graph database
(Neo4j), and run via HPC workload schedulers (Slurm or Flux).

- Package name (PyPI): `hpc-beeflow`
- Python package: `beeflow`
- Repository: https://github.com/lanl/BEE
- License: open source, BEE C17056 (see `LICENSE`)
- Contact: bee-dev@lanl.gov

## Repository Layout

```
beeflow/                 Main Python package
  client/                CLI entry point (bee_client.py), core.py, remote_client.py
  common/                Shared code: config, CWL parser, graph db (gdb), workers,
                         container runtimes (crt), cloud, build, integration
  wf_manager/            Workflow Manager service (Flask/REST)
  task_manager/          Task Manager service (submits jobs to Slurm/Flux)
  remote/                Remote execution support
  data/                  CWL examples, dockerfiles, cloud templates
  tests/                 pytest unit tests
ci/                      Shell scripts + integration tests used in CI
docs/                    Sphinx documentation and topic READMEs
examples/                Example workflows
.github/workflows/       CI: pylint.yml, testing-coverage-docs.yml, tag-docs.yml
```

## Environment & Tooling

- **Python:** `>=3.11,<=3.14`
- **Dependency/venv manager:** [Poetry](https://python-poetry.org/)
- **CLI command:** `beeflow` (maps to `beeflow.client.bee_client:main`)

Install for development:

```sh
poetry install
poetry shell        # activate the environment
```

## Testing

Unit tests use **pytest** and live in `beeflow/tests/`.

```sh
# Run the full unit test suite
pytest beeflow/tests/

# Run with coverage (matches CI)
pytest --cov=beeflow beeflow/tests/

# Run a single test file
pytest beeflow/tests/test_wf_manager.py
```

CI wraps these in `ci/unit_tests.sh`. Integration tests are driven by
`ci/integration_test.py` / `ci/integration_test.sh` and require Slurm/Flux and
container runtimes, so they are not typically run locally.

## Code Style & Linting

The project enforces style with **pylint**, configured in `setup.cfg`:

- Max line length: **99**
- See `setup.cfg` `[pylint]` for allowed `good-names` and disabled checks.
- `data` and `examples` directories are excluded from linting.

Run pylint before committing:

```sh
pylint --rcfile=setup.cfg beeflow
```

### Pre-commit hooks

A `pre-commit` config (`.pre-commit-config.yaml`) runs pylint on staged Python
files. Install the git hooks after cloning:

```sh
# git >= 2.9
git config core.hooksPath .githooks
# otherwise
cp .githooks/* .git/hooks/
```

## Documentation

Docs are built with Sphinx (see `docs/README.md`):

```sh
poetry shell
cd docs/sphinx
make html
open _build/html/index.html
```

## Guidelines for Agents

- Match existing conventions; keep lines within the 99-character pylint limit.
- Only use dependencies already declared in `pyproject.toml`. If a new dependency
  is truly needed, add it via Poetry and explain why.
- Add or update pytest tests in `beeflow/tests/` for behavior changes, and run
  `pytest beeflow/tests/` plus `pylint --rcfile=setup.cfg beeflow` before finishing.
- Prefer small, focused changes; do not reformat unrelated code.
- The default working branch is `develop`; open PRs against it.
- Update relevant docs (`docs/`, module `README.md` files) when behavior changes.
