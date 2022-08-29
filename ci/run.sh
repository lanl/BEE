#!/bin/sh
# Wrapper script to run everything with the proper environment

. ./ci/env.sh
. ./venv/bin/activate
poetry run $@
