#!/bin/sh
# Setup and install BEE.

set -e

# BEE Containers
printf "\n\n"
printf "**Setting up BEE containers**\n"
printf "\n\n"
mkdir -p $HOME/img
# Pull the Neo4j container
#chmod +x ./beeflow/data/dockerfiles/Dockerfile.neo4j 
ch-image build -t neo4j_image -f ./beeflow/data/dockerfiles/Dockerfile.neo4j ./ci || exit 1
ch-convert -i ch-image -o tar neo4j_image $NEO4J_CONTAINER || exit 1
# Pull the Redis container
ch-image pull redis || exit 1
ch-convert -i ch-image -o tar redis $REDIS_CONTAINER || exit 1

# BEE install
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
# Do a poetry install, making sure that all extras are added
poetry install -E cloud_extras || exit 1
