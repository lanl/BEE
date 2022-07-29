#!/bin/sh
# Set up and start Slurm

. ./ci/env.sh

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
