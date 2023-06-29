#!/bin/sh
# Setup and install BEE.

. ./ci/env.sh

set -e

# BEE Containers
printf "\n\n"
printf "**Setting up BEE containers**\n"
printf "\n\n"
mkdir -p $HOME/img
# Pull the neo4j container
ch-image pull neo4j:3.5.22 || exit 1
ch-convert -i ch-image -o tar neo4j:3.5.22 $NEO4J_CONTAINER || exit 1

# BEE install
printf "\n\n"
printf "**Installing BEE**\n"
printf "\n\n"
$PYTHON -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install poetry
# Do a poetry install, making sure that all extras are added
poetry install -E cloud_extras || exit 1

