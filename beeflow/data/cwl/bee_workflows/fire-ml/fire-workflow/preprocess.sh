#!/bin/sh
# Wrapper to make sure the environment is set up

. /venv/bin/activate
python3 /preprocess.py "$@"

