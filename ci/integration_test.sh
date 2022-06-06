#!/bin/sh
# Install dependencies
sudo apt-get update
sudo apt-get install -y slurmctld slurmd slurmrestd munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev

# Install most recent Charliecloud
curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.27/charliecloud-0.27.tar.gz
tar -xvf charliecloud-0.27.tar.gz
(cd charliecloud-0.27
 ./configure --prefix=/usr
 make
 sudo make install)
# Use a PPA to install Python3.8
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.8 python3.8-dev python3.8-venv
# Set the default python
sudo update-alternatives --set python /usr/bin/python3.8

# Set up environment
PYTHON=python3.8
HOSTNAME=`python -c 'import socket; print(socket.gethostname())'`
# Everything is in /tmp for right now
SLURMCTLD_PID=/tmp/slurmctld.pid
SLURMD_PID=/tmp/slurmd.pid
SLURMD_SPOOL_DIR=/tmp/slurm_spool
LOG_DIR=/tmp/slurm_log
SLURM_STATE_SAVE_LOCATION=/tmp/slurm_state
mkdir -p $SLURMD_SPOOL_DIR $SLURM_STATE_SAVE_LOCATION $LOG_DIR
SLURMCTLD_LOG=$LOG_DIR/slurmctld.log
SLURMD_LOG=$LOG_DIR/slurmd.log
SLURM_USER=`whoami`
MUNGE_SOCKET=/tmp/munge.sock
MUNGE_LOG=/tmp/munge.log
MUNGE_PID=/tmp/munge.pid
mkdir -p /tmp/munge
MUNGE_KEY=/tmp/munge/munge.key
# Determine config of CI host
NODE_CONFIG=`slurmd -C | head -n 1`
BEE_WORKDIR=$HOME/.beeflow
mkdir -p $BEE_WORKDIR

export SLURM_CONF=~/slurm.conf

# Dump a new slurm.conf
cat >> $SLURM_CONF <<EOF
ClusterName=bee-ci
# For some reason pmix is missing
# MpiDefault=pmix
MpiDefault=none
ProctrackType=proctrack/pgid
ReturnToService=2
SlurmctldPort=7777
SlurmdPort=8989

SwitchType=switch/none

TaskPlugin=task/affinity

InactiveLimit=0
KillWait=30
MinJobAge=300
Waittime=0

SchedulerType=sched/backfill
SelectType=select/cons_tres
SelectTypeParameters=CR_Core

AccountingStorageType=accounting_storage/none
JobCompType=jobcomp/none
JobAcctGatherType=jobacct_gather/none
SlurmdDebug=info
AuthType=auth/munge

SlurmctldHost=$HOSTNAME
SlurmctldPidFile=$SLURMCTLD_PID
SlurmdPidFile=$SLURMD_PID
StateSaveLocation=$SLURM_STATE_SAVE_LOCATION
SlurmdSpoolDir=$SLURMD_SPOOL_DIR
SlurmctldLogFile=$SLURMCTLD_LOG
SlurmdLogFile=$SLURMD_LOG
SlurmUser=$SLURM_USER
SlurmdUser=$SLURM_USER
AuthInfo=socket=$MUNGE_SOCKET

$NODE_CONFIG
PartitionName=debug Nodes=ALL Default=YES MaxTime=INFINITE State=UP
EOF

printf "\n\n"
printf "#### slurm.conf ####\n"
cat $SLURM_CONF
printf "#### slurm.conf ####\n"
printf "\n\n"

# Start daemons
printf "**Starting munged**\n"
# Create the key
head -c 1024 /dev/urandom > $MUNGE_KEY
chmod 400 $MUNGE_KEY
munged -f \
    -S $MUNGE_SOCKET \
    --log-file $MUNGE_LOG \
    --pid-file $MUNGE_PID \
    --key-file $MUNGE_KEY
sleep 1
printf "**Starting slurmctld**\n"
slurmctld
printf "**Starting slurmd**\n"
slurmd

printf "#### SUPPORTED MPI ####\n"
srun --mpi=list
printf "#######################\n"

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
poetry install || exit 1

# BEE Configuration
mkdir -p ~/.config/beeflow
JOB_TEMPLATE=$HOME/.config/beeflow/submit.jinja
cp src/beeflow/data/job_templates/slurm-submit.jinja $JOB_TEMPLATE
cat >> ~/.config/beeflow/bee.conf <<EOF
# BEE CONFIGURATION FILE #
[DEFAULT]
bee_workdir = $BEE_WORKDIR
workload_scheduler = Slurm
use_archive = False
bee_dep_image = $NEO4J_CONTAINER

[task_manager]
listen_port = 8892
container_runtime = Charliecloud
job_template = $JOB_TEMPLATE
runner_opts =

[charliecloud]
image_mntdir = /tmp
chrun_opts = --cd $HOME
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
listen_port = 5100
use_mars = False
mars_model =
mars_task_cnt = 3
alloc_logfile = $BEE_WORKDIR/logs/scheduler_alloc.log
algorithm = fcfs
default_algorithm = fcfs
workdir = $BEE_WORKDIR/scheduler

[workflow_manager]
listen_port = 7233

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

# Try to run BEE
printf "\n\n"
printf "**Starting BEE**\n"

# Slurmrestd will fail by default when running as `SlurmUser`
SLURMRESTD_SECURITY=disable_user_check beeflow || exit 1

sleep 4

# Start the actual integration tests
./ci/integration_test.py

# Output the logs for CI
for log in $SLURMCTLD_LOG $SLURMD_LOG $MUNGE_LOG $BEE_WORKDIR/logs/*; do
    printf "\n\n"
    printf "#### $log ####\n"
    cat $log
    printf "#### $log ####\n"
    printf "\n\n"
done
