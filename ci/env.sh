# Environment set up
# Set up environment
export PYTHON=python3
export HOSTNAME=`$PYTHON -c 'import socket; print(socket.gethostname())'`
# Everything is in /tmp for right now
export SLURMCTLD_PID=/tmp/slurmctld.pid
export SLURMD_PID=/tmp/slurmd.pid
export SLURMD_SPOOL_DIR=/tmp/slurm_spool
export LOG_DIR=/tmp/slurm_log
export SLURM_STATE_SAVE_LOCATION=/tmp/slurm_state
mkdir -p $SLURMD_SPOOL_DIR $SLURM_STATE_SAVE_LOCATION $LOG_DIR
export SLURMCTLD_LOG=$LOG_DIR/slurmctld.log
export SLURMD_LOG=$LOG_DIR/slurmd.log
export SLURM_USER=`whoami`
export MUNGE_SOCKET=/tmp/munge.sock
export MUNGE_LOG=/tmp/munge.log
export MUNGE_PID=/tmp/munge.pid
mkdir -p /tmp/munge
export MUNGE_KEY=/tmp/munge/munge.key
# Determine config of CI host
export NODE_CONFIG=`slurmd -C | head -n 1`
export BEE_WORKDIR=$HOME/.beeflow
export NEO4J_CONTAINER=$HOME/img/neo4j.tar.gz
export REDIS_CONTAINER=$HOME/img/redis.tar.gz
mkdir -p $BEE_WORKDIR
export SLURM_CONF=~/slurm.conf
# Flux variables
export FLUX_CORE_VERSION=0.51.0
export FLUX_SECURITY_VERSION=0.9.0
export BEE_CONFIG=$HOME/.config/beeflow/bee.conf
export OPENAPI_VERSION=v0.0.37
export CHARLIECLOUD_VERSION=0.36
