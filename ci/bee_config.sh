#!/bin/sh
# BEE Configuration

case $BEE_WORKER in
Slurm*)
    export WORKLOAD_SCHEDULER=Slurm
    ;;
Flux)
    export WORKLOAD_SCHEDULER=Flux
    ;;
esac

mkdir -p $(dirname $BEE_CONFIG)
cat >> $BEE_CONFIG <<EOF
# BEE CONFIGURATION FILE #
[DEFAULT]
bee_workdir = $BEE_WORKDIR
workload_scheduler = $WORKLOAD_SCHEDULER
neo4j_image = $NEO4J_CONTAINER
redis_image = $REDIS_CONTAINER
max_restarts = 2

[task_manager]
container_runtime = Charliecloud
runner_opts =
background_interval = 2

[charliecloud]
image_mntdir = /tmp
chrun_opts = --home
setup =

[job]
default_account =
default_time_limit =
default_partition =

[graphdb]
hostname = localhost
dbpass = password
bolt_port = 7687
http_port = 7474
https_port = 7473
gdb_image_mntdir = /tmp
sleep_time = 10

[scheduler]
algorithm = fcfs
default_algorithm = fcfs

[workflow_manager]

[builder]
deployed_image_root = /tmp
container_output_path = /tmp
container_type = charliecloud
container_archive = $BEE_WORKDIR/container_archive
EOF

case $BEE_WORKER in
Slurmrestd)
    cat >> $BEE_CONFIG <<EOF
[slurm]
use_commands = True
openapi_version = $OPENAPI_VERSION
EOF
    ;;
SlurmCommands)
    cat >> $BEE_CONFIG <<EOF
[slurm]
use_commands = True
openapi_version = $OPENAPI_VERSION
EOF
    ;;
esac

printf "\n\n"
printf "#### %s ####\n" $BEE_CONFIG
cat $BEE_CONFIG
printf "#### %s ####\n" $BEE_CONFIG
printf "\n\n"
