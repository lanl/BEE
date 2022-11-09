#!/bin/sh
# Setup and install BEE.

. ./ci/env.sh

set -e

# BEE Containers
printf "\n\n"
printf "**Setting up BEE containers**\n"
printf "\n\n"
mkdir -p $HOME/img
# Pull the neo4j container
ch-image pull neo4j:3.5.22 || exit 1
NEO4J_CONTAINER=$HOME/img/neo4j.tar.gz
ch-convert -i ch-image -o tar neo4j:3.5.22 $NEO4J_CONTAINER || exit 1

# BEE install
printf "\n\n"
printf "**Installing BEE**\n"
printf "\n\n"
$PYTHON -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install poetry
# Do a poetry install, making sure that all extras are added
poetry install -E cloud_extras || exit 1

# BEE Configuration
mkdir -p ~/.config/beeflow
JOB_TEMPLATE=$HOME/.config/beeflow/submit.jinja
cp beeflow/data/job_templates/slurm-submit.jinja $JOB_TEMPLATE
cat >> ~/.config/beeflow/bee.conf <<EOF
# BEE CONFIGURATION FILE #
[DEFAULT]
bee_workdir = $BEE_WORKDIR
workload_scheduler = Slurm
use_archive = False
bee_dep_image = $NEO4J_CONTAINER
beeflow_pidfile = $HOME/beeflow.pid
beeflow_socket = $HOME/beeflow.sock

[task_manager]
socket = $HOME/tm.sock
container_runtime = Charliecloud
job_template = $JOB_TEMPLATE
runner_opts =

[charliecloud]
image_mntdir = /tmp
chrun_opts =
setup =

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
use_mars = False
mars_model =
mars_task_cnt = 3
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

[slurmrestd]
slurm_socket = /tmp/slurm.sock
slurm_args = -s openapi/v0.0.35
EOF
printf "\n\n"
printf "#### bee.conf ####\n"
cat ~/.config/beeflow/bee.conf
printf "#### bee.conf ####\n"
printf "\n\n"
