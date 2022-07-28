#!/bin/sh
# Start BEE

. ./ci/env.sh
. venv/bin/activate
# Slurmrestd will fail by default when running as `SlurmUser`
SLURMRESTD_SECURITY=disable_user_check beeflow || exit 1
sleep 4
