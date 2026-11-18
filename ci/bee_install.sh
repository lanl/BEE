#!/bin/sh
# Install BEE.

set -e

printf "\n\n"
printf "**Installing BEE**\n"
printf "\n\n"
$PYTHON -m venv venv
. venv/bin/activate
pip install --upgrade pip
# pip install poetry
# TODO: May want to use pip with specific version here
curl -L https://install.python-poetry.org/ > install-poetry.sh
chmod +x install-poetry.sh
./install-poetry.sh
# Integration fixtures include legacy CWL workflows; request compatibility explicitly.
poetry install --extras cwl || exit 1
