#!/bin/sh
# Set up and start the batch scheduler

case $BATCH_SCHEDULER in
Slurm)
    ./ci/slurm_start.sh
    ;;
Flux)
    ./ci/flux_install.sh
    ;;
*)
    printf "ERROR: Invalid batch scheduler '%s'\n" "$BATCH_SCHEDULER"
    ;;
esac
