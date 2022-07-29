# Environment set up
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