#!/bin/sh
# BEE Configuration for Slurm

. ./ci/env.sh

mkdir -p ~/.config/beeflow
cat >> ~/.config/beeflow/bee.conf <<EOF
# BEE CONFIGURATION FILE #
[DEFAULT]
bee_workdir = $BEE_WORKDIR
workload_scheduler = Slurm
use_archive = False
bee_dep_image = $NEO4J_CONTAINER
beeflow_pidfile = $HOME/beeflow.pid
beeflow_socket = $HOME/beeflow.sock
max_restarts = 2

[task_manager]
socket = $HOME/tm.sock
container_runtime = Charliecloud
runner_opts =

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
log = $BEE_WORKDIR/logs/scheduler.log
socket = $HOME/scheduler.sock
alloc_logfile = $BEE_WORKDIR/logs/scheduler_alloc.log
algorithm = fcfs
default_algorithm = fcfs
workdir = $BEE_WORKDIR/scheduler

[workflow_manager]
socket = $HOME/wf_manager.sock

[builder]
deployed_image_root = /tmp
container_output_path = /tmp
container_type = charliecloud
container_archive = $HOME/container_archive

[slurm]
# Just test slurmrestd in CI for now
use_commands = False
slurmrestd_socket = /tmp/slurm.sock
openapi_version = v0.0.37
EOF
printf "\n\n"
printf "#### bee.conf ####\n"
cat ~/.config/beeflow/bee.conf
printf "#### bee.conf ####\n"
printf "\n\n"
