Pipenv Quickstart Guide
-----------------------
To conform to our coding standards, it is most convenient to use Pipenv
to install a virtual environment with all of our utilized linting packages
and our project's dependencies.

Installation
============
MacOS: `brew install pipenv`

Debian/Ubuntu: `sudo apt install pipenv`

Fedora 28: `sudo dnf install pipenv`

FreeBSD: `pkg install py36-pipenv`

Pipenv Commands
===============
All of the following commands should be run in the root of our
project directory.

### Create a Python Virtual Environment
To create a Python 3.x virtual environment:
```pipenv --three```

### Install Project Packages/Dependencies
To install our development packages and software project depenencies:
```pipenv sync```

### Activate the Virtual Environment
To activate the virtual environment ('exit' or EOF to deactivate):
```pipenv shell```

### Run a Command in the Virtual Environment
To run a command without activating the virtual environment:
```pipenv run COMMAND [arguments]```

And that's it!