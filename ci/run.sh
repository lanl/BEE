#!/bin/sh
# Wrapper script to run everything with the proper environment

. ./ci/env.sh
poetry run $@
