#!/bin/sh
# Start BEE
set -e
. ./ci/env.sh
. venv/bin/activate
# Slurmrestd will fail by default when running as `SlurmUser`
SLURMRESTD_SECURITY=disable_user_check beeflow start
sleep 4

for log in $BEE_WORKDIR/logs/*.log; do
    printf "### $log ###\n"
    cat $log
    printf "################################################################################\n"
done

beeflow status
