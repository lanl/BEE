# Poetry Tutorial
Poetry is our main tool for managing dependencies and packaging.
The following are explanations of the most common use cases in Poetry version 1.0.0.

## New Python Project
Create a new Poetry project with a basic `pyproject.toml` file:

`poetry new <pkg-name>`

This creates the following file structure:
```
pkg-name
├── pyproject.toml
├── README.rst
├── pkg-name
│   └── __init__.py
└── tests
    ├── __init__.py
    └── test_pkg-name.py
```

## New Basic Poetry Project
Interactively create a new `pyproject.toml` file in the current directory:

`poetry init`

## Add/Remove Dependencies
Add Python package dependencies (from PyPI) to `pyproject.toml`:

`poetry add <pkg-name>...`

Add developer dependencies (e.g. `pylint`, `sphinx`):

`poetry add --dev <pkg-name>...`

Add package Git dependency (from `master` branch by default):

`poetry add git+https://github.com/<owner>/<repo>.git`

Add package Git dependency from a specific branch:

`poetry add git+https://github.com/<owner>/<repo>.git#<branch>`

Remove package dependencies:

`poetry remove <pkg-name>...`

Remove developer dependencies:

`poetry remove --dev <pkg-name>...`

## Install/Remove Dependencies
Search for a Python package from a remote repository (e.g. PyPI):

`poetry search <pkg-name>`

Install all package and developer dependencies (and build the `beeflow` package):

`poetry install`

Install only package dependencies (and build the `beeflow` package):

`poetry install --no-dev`

In either case, building the `beeflow` package will add the project root directory (i.e. BEE_Private) to
`sys.path`, which permits absolute imports of modules within this directory
(e.g. `import beeflow.common.wf_interface`, `python -m unittest test.test_wf_interface`).

If `poetry.lock` exists in the project directory, the specific versions of each package specified inside are installed.
Otherwise, the most up-to-date package version subject to the version constraints given in `pyproject.toml` is installed.

## List Installed Dependencies
List all installed package and developer dependencies and sub-dependencies:

`poetry show`

List only package dependencies and sub-dependencies:

`poetry show --no-dev`

## Update Dependencies (or Poetry)
Update all package and developer dependencies:

`poetry update`

Update only package dependencies:

`poetry update --no-dev`

Update specific dependencies:

`poetry update <pkg-name>...`

Update Poetry (Poetry must be installed using the [recommended installer](https://python-poetry.org/docs/#installation)):

`poetry self update`

## Build the Project Package
Build the project package, creating a tarball and a wheel/egg:

`poetry build`

## Manage/Display the Python Environment(s)
Display information about the active Python environment:

`poetry env info`

List all Python virtual environments associated with the project:

`poetry env list`

Add or create a new Python virtual environment associated with the project:

`poetry use <path/to/python>`

Remove a Python virtual environment associated with the project:

`poetry remove <path/to/python>`

## Activate the Current Poetry Virtual Environment
Spawn a shell within the current Python virtual environment (see `poetry env list`):

`poetry shell`

## Run a Command in the Poetry Virtual Environment
Execute a command inside the current Python virtual environment (see `poetry env list`):

`poetry run <command> [args]...`

## Get Poetry Help
Display Poetry help message with list of subcommands:

`poetry help`

Display help for a specific subcommand:

`poetry help <subcommand>`

Additional help can be found [here](https://python-poetry.org/docs/).
