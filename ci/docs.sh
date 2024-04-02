#!/bin/sh
# Install BEE and build the docs in CI.
sudo apt-get update
sudo apt-get install python3 python3-venv curl build-essential \
    zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libsqlite3-dev \
    libreadline-dev libffi-dev libbz2-dev libyaml-dev
curl -sSL https://install.python-poetry.org | python3 -
poetry update
poetry install
poetry run make -C docs/sphinx html
