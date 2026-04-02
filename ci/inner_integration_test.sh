#!/bin/sh
# Actual integration test runner

. ./ci/env.sh
. venv/bin/activate

set +e

printf "#### RUNNING PROCESSES ####\n"
ps aux
printf "#### TEST JOB SUBMISSION ####\n"
salloc echo test

# BEE needs to be started here in order to access batch scheduler resources
case $BEE_WORKER in
Slurmrestd)
    # Slurmrestd will fail by default when running as `SlurmUser`
    SLURMRESTD_SECURITY=disable_user_check beeflow core start
    ;;
*)
    beeflow core start
    ;;
esac
sleep 4

# Start the actual integration tests
./ci/integration_test.py
# Save the exit code for later
EXIT_CODE=$?

# Output the status logs
beeflow core status

for log in $BEE_WORKDIR/logs/*.log; do
    printf "### $log ###\n"
    cat $log
    printf "################################################################################\n"
done

exit $EXIT_CODE
