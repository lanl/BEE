Pipenv Quickstart Guide
=======================
To conform to our coding standards, it is most convenient to use Pipenv
to install a virtual environment with all of our utilized linting packages
and our project's dependencies. Pipenv uses the `Pipfile` and `Pipfile.lock`
files to manage our packages/dependencies and make it easy to automatically
install them to our virtual environment.

Installation
------------
MacOS: `brew install pipenv`

Debian/Ubuntu: `sudo apt install pipenv`

Fedora 28: `sudo dnf install pipenv`

FreeBSD: `pkg install py36-pipenv`

Pipenv Commands
---------------
All of the following commands should be run in the root of our
project directory.

### Create a Python Virtual Environment
To create a Python 3.x virtual environment:

`pipenv --three`

This will search your PATH for an instance of `python3`, using that version
of Python for the virtual environment. If you have multiple versions of
Python 3.x installed, you can specify a certain one using the command:

`pipenv --python /path/to/python`

Pipenv virtual enviornments are installed to `~/.local/share/virtualenvs`.

---

### Install Project Packages/Dependencies
To install our development packages and software project depenencies:

`pipenv install`

---

### Activate the Virtual Environment
To activate the virtual environment ('exit' or EOF to deactivate):

`pipenv shell`

---

### Run a Command in the Virtual Environment
To run a command without activating the virtual environment:

`pipenv run COMMAND [arguments]`

---

And that's it!
