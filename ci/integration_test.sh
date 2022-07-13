#!/bin/sh

. ./ci/env.sh

# Start the actual integration tests
./ci/integration_test.py
# Save the exit code for later
EXIT_CODE=$?

# Output the logs
for log in $SLURMCTLD_LOG $SLURMD_LOG $MUNGE_LOG $BEE_WORKDIR/logs/*; do
    printf "\n\n"
    printf "#### $log ####\n"
    cat $log
    printf "#### $log ####\n"
    printf "\n\n"
done

exit $EXIT_CODE
