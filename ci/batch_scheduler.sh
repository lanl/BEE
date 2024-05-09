#!/bin/sh
# Set up and start the batch scheduler

case $BEE_WORKER in
Slurmrestd|SlurmCommands)
    ./ci/slurm_start.sh
    ;;
Flux)
    ./ci/flux_install.sh
    ;;
*)
    printf "ERROR: Invalid worker type '%s'\n" "$BEE_WORKER"
    exit 1
    ;;
esac
