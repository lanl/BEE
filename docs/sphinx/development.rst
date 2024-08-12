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

Additional Poetry documentation:

* https://poetry.eustace.io/docs/

* https://github.com/sdispater/poetry

Requirement: Python version 3.8 or greater
------------------------------------------

Installation
------------
It is possible to install Poetry using Pip, but it is recommended to instead
install it via a script using the following command:

`curl -sSL https://install.python-poetry.org | python3 -`

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

On MacOS, Poetry virtual environments are installed to `~/Library/Caches/pypoetry/virtualenvs`.
To instead install to a local `.venv` directory, first run the command:

`poetry config settings.virtualenvs.in-project true`

When creating a Python virtual environment, Poetry will automatically install the version of Python of whatever `python` executable appears first on your PATH.


Development Workflow
====================

1. Make changes
---------------
To work on a fix or feature, switch to the feature branch in the BEE repo (see :ref:`contribute`).

2. Create a Virtual Environment and Install Dependencies
---------------------------------------------------------

After making your changes create a Python 3.x virtual environment and install our project
dependencies (including developer dependencies):

``poetry install``

3. Activate the Virtual Environment
-----------------------------------

To activate the virtual environment ('exit' or EOF to deactivate):

``poetry shell``

4. Start the BEE components
---------------------------

``beeflow core start``

5. Test
---------

Test your new feature/fixes

6. Commit Changes
-----------------

If you're done making changes, follow the git workflow specified in :ref:`contribute`.

7. Continue Development
-----------------------

If you want to continue making changes, add them and then pause any running workflows:

``beeflow pause $ID``

Stop the bee components:

``beeflow core stop``

Now you can repeat steps 2 to 5.


Dependency and Package Management with Poetry
=============================================

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


Running Tests
==================

BEE includes unit and integration tests that can be run on a local system.

To run the unit tests, make sure to install beeflow with ``poetry install -E cloud_extras``; the ``-E cloud_extras`` option forces Poetry to install extra dependencies required for some of the cloud API tests. After loading a shell with ``poetry shell``, you can run the unit tests with ``pytest beeflow/tests``.

For the integration tests, you'll first have to start beeflow with ``beeflow core start`` (see :ref:`command-line-interface`). Then, making sure that you have Charliecloud loaded in your environment, you can run ``./ci/integration_test.py`` to run the tests. This must be done from the root of BEE repository. The integration tests will create a directory ``~/.beeflow-integration`` to be used for storing temporary files as well as inspecting failure results. The script itself includes a number of options for running extra tests, details of which can be found through ``--help`` and other command line options. Running the script without any options will run the default test suite. Some tests are disabled by default due to runtime or environment constraints and need to be specified in a comma-separated list with ``--tests`` (``-t``) to be run. Run the script with just ``--show-tests`` (``-s``) to see a list of all possible tests.
