#!/bin/sh

. venv/bin/activate

set +e

case $BEE_WORKER in
Slurm*)
    ./ci/inner_integration_test.sh
    EXIT_CODE=$?
    ;;
Flux)
    flux start --test-size=1 ./ci/inner_integration_test.sh
    EXIT_CODE=$?
    ;;
*)
    printf "ERROR: Invalid batch scheduler option '%s'\n" "$BEE_WORKER"
    ;;
esac

for log in $SLURMCTLD_LOG $SLURMD_LOG $MUNGE_LOG $BEE_WORKDIR/logs/*; do
    printf "\n\n"
    printf "#### $log ####\n"
    cat $log
    printf "#### $log ####\n"
    printf "\n\n"
done

exit $EXIT_CODE
