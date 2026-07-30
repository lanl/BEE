#!/bin/sh
# Setup BEE

set -e

# BEE Containers
printf "\n\n"
printf "**Setting up BEE containers**\n"
printf "\n\n"
mkdir -p $HOME/img
# Build the Neo4j container
ch-image build -t neo4j_image -f ./beeflow/data/dockerfiles/Dockerfile.neo4j ./ci || exit 1
ch-convert -i ch-image -o tar neo4j_image $NEO4J_CONTAINER || exit 1
# Pull the Redis container
ch-image pull redis || exit 1
ch-convert -i ch-image -o tar redis $REDIS_CONTAINER || exit 1

