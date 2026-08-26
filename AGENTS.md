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

```text
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
- **Dependency/package manager:** [Poetry](https://python-poetry.org/)
- **CLI command:** `beeflow` (maps to `beeflow.client.bee_client:main`)

For development, use a Python virtual environment and use Poetry for dependency
installation and project packaging. The docs advise against using
`poetry env activate` or `poetry shell`, and instead recommend using Poetry
only for dependency installation.

Example setup:

```sh
mkdir beedev-env
python3 -m venv beedev-env
source beedev-env/bin/activate
pip install poetry
cd <path to BEE repo>
poetry install
beeflow --version
```

To leave the environment:

```sh
deactivate
```

## Installation Notes

Runtime installation for users is typically via pip:

```sh
pip install hpc-beeflow
```

BEE has the following installation/runtime requirements documented in
`docs/sphinx/installation.rst`:

- Python 3.11 to 3.14
- Charliecloud 0.34 or greater
- Two Charliecloud dependency containers: Neo4j 5.x and Redis
- Config file location:
  - Linux: `~/.config/beeflow/bee.conf`
  - macOS: `~/Library/Application Support/beeflow/bee.conf`

Useful operational commands:

```sh
beeflow config new
beeflow core pull-deps
beeflow core start
beeflow core status
beeflow core stop
```

Some HPC systems have multiple front-ends; run workflows and BEE components on
the same front end.

## Testing

Unit tests use **pytest** and live in `beeflow/tests/`.

```sh
# Run the full unit test suite
pytest beeflow/tests/

# Run with coverage details
pytest --cov=beeflow --cov-report term-missing beeflow/tests/

# Run a single test file
pytest beeflow/tests/test_wf_manager.py
```

Helpful pytest features called out in the developer docs:

- `@pytest.mark.parametrize`
- `tmp_path`
- `mocker`
- `-k EXPRESSION`
- `--durations 0`

Attempt to write tests that cover all new/modified lines. Test files should be
named `test_MODULE_NAME.py`, and test functions should begin with `test_`.

Integration tests can be run locally, but they require BEE components to be
started first. The developer docs also call out that Charliecloud must be
loaded in the environment before running them:

```sh
beeflow core start
./ci/integration_test.py
```

The integration test runner supports options such as `--help`, `--show-tests`,
and `--tests` for selecting additional disabled-by-default tests.

## Code Style & Linting

BEE follows Python style rules configured in `setup.cfg` and enforced with
**pylint**.

- Max line length: **99**
- See `setup.cfg` `[pylint]` for allowed `good-names` and disabled checks.
- `data` and `examples` directories are excluded from linting.

Run pylint before committing:

```sh
pylint --rcfile=setup.cfg beeflow
```

### Pre-commit hooks

The contributor docs now instruct developers to install hooks with:

```sh
pre-commit install
```

Notes:

- The Python environment must have BEE dependencies installed so hooks can run.
- To skip the pylint hook for one commit:

```sh
SKIP=pylint git commit -m "message"
```

## Documentation

Docs are built with Sphinx.

```sh
cd docs/sphinx
make html
```

## Git Workflow

BEE has two lifetime branches: `develop` and `main`.

- Create fix/feature branches from `develop`.
- Branches should address an open issue and follow the format
  `issue#/title` (example: `issue857/mpi-integration-test`).
- Open pull requests from feature/issue branches into `develop`.
- Open a work-in-progress PR labeled `WIP`.
- Before requesting approval, merge `develop` into your branch and resolve any
  conflicts.
- Remove the `WIP` label when the PR is ready for final review.
- GitHub CI tests must pass before merging into `develop`.
- Releases are merged from `develop` into `main` by the team lead, and changes
  must also pass overnight tests before merging into `main`.

## Guidelines for Agents

- Match existing conventions; keep lines within the 99-character pylint limit.
- Only use dependencies already declared in `pyproject.toml`. If a new dependency
  is truly needed, add it via Poetry and explain why.
- Add or update pytest tests in `beeflow/tests/` for behavior changes, and run
  relevant tests plus `pylint --rcfile=setup.cfg beeflow` before finishing.
- Prefer small, focused changes; do not reformat unrelated code.
- Use the documented Git workflow: branch from `develop`, follow the
  `issue#/title` naming convention, and target PRs to `develop`.
- Update relevant docs (`docs/`, module `README.md` files) when behavior changes.
- If work requires running BEE services or integration tests, use the documented
  lifecycle commands such as `beeflow core start` and `beeflow core stop`.
