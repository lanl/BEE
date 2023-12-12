#!/bin/sh
# Actual integration test runner

. ./ci/env.sh
. venv/bin/activate

set +e

# BEE needs to be started here in order to access batch scheduler resources
if [ "$BATCH_SCHEDULER" = "Slurm" ]; then
    # Slurmrestd will fail by default when running as `SlurmUser`
    SLURMRESTD_SECURITY=disable_user_check beeflow core start
else
    beeflow core start
fi
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
