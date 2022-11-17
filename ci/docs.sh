#!/bin/sh

set -e
. ./ci/env.sh
. venv/bin/activate
# This builds the docs in docs/sphinx/_build/html
make -C docs/sphinx html
