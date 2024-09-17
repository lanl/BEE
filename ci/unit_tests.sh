#!/bin/sh

. ./venv/bin/activate

# Needed to run slurmrestd in CI
export SLURMRESTD_SECURITY=disable_user_check

pytest beeflow/tests/

#Get coverage report
pytest --cov=beeflow beeflow/tests/
