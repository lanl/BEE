#!/bin/sh

. ./venv/bin/activate
. ./ci/env.sh

# Needed to run slurmrestd in CI
export SLURMRESTD_SECURITY=disable_user_check

pytest beeflow/tests/
