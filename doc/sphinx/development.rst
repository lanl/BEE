Developer's Guide
#################
Poetry Setup Guide
==================
To manage our development environment and configure our project packaging,
it is most convenient to use Poetry. Poetry uses the `pyproject.toml` and `poetry.lock`
files to manage our packages/dependencies and make it easy to automatically
install them to a virtual environment. It also makes it easy to build and
install our package locally as well as publish it to PyPI, obviating the need
for a `setup.py` file.

Requirement: Python version 3.8 or greater
------------------------------------------

Installation
------------
It is possible to install Poetry using Pip, but it is recommended to instead
install it via a script using the following command:

`curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python3`

This will install Poetry to `~/.poetry/bin`, which should be automatically prepended to your PATH
by modifying your `~/.profile`, `~/.bash_profile`, and/or `~/.bashrc`. If you are using a
shell other than Bash, you will have to add it to your PATH manually.

Environment Setup
-----------------
All of the following commands should be run in the root of our
project directory as that is where our `.python-version`, `pyproject.toml`, and
`poetry.lock` files are located (for use with Pyenv).

**If you use Pyenv**, change the line in your `~/.bashrc`, etc.:

`eval "$(pyenv init -)"`

to:

`[ $POETRY_ACTIVE ] || eval "$(pyenv init -)"`

Create a Virtual Environment and Install Dependencies
-----------------------------------------------------
On MacOS, Poetry virtual environments are installed to `~/Library/Caches/pypoetry/virtualenvs`.
To instead install to a local `.venv` directory, first run the command:

`poetry config settings.virtualenvs.in-project true`

When creating a Python virtual environment, Poetry will automatically install the version of Python of whatever `python` executable appears first on your PATH.

To create a Python 3.x virtual environment and install our project
dependencies (including developer dependencies):

`poetry install`

To install without developer dependencies:

`poetry install --no-dev`

This will also generate the package metadata in `beeflow.egg-info` (not tracked) and install
the package to your local system as a Python Egg.


Activate the Virtual Environment
-----------------------------------------------------
To activate the virtual environment ('exit' or EOF to deactivate):

`poetry shell`


Run a Command in the Virtual Environment
-----------------------------------------------------
To run a command without activating the virtual environment:

`poetry run COMMAND [arguments]`


Update Dependencies
-----------------------------------------------------
To update the package dependencies and generate a new `poetry.lock` (tracked):

`poetry update`


Add a New Dependency
-----------------------------------------------------
To add a new dependency to `pyproject.toml`:

`poetry add <package>`


Remove a Dependency
-----------------------------------------------------
To remove a dependency from `pyproject.toml`:

`poetry remove <package>`


Build the Package
-----------------------------------------------------
To build the package as a tarball and a wheel (by default):

`poetry build`


Check the Validity of pyproject.toml
-----------------------------------------------------

`poetry check`


Publish the Package to a Remote Repository
-----------------------------------------------------

`poetry publish`


Update Poetry
-----------------------------------------------------
To update Poetry:

`poetry self:update`

Additional Documentation
------------------------
Additional documentation:

* https://poetry.eustace.io/docs/

* https://github.com/sdispater/poetry

