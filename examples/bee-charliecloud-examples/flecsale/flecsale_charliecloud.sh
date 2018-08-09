#!/usr/bin/env bash
module purge
module load charliecloud openmpi/2.1.2-gcc_7.3.0
module list
mkdir -p output
srun ch-tar2dir /scratch/beedev/flecsale_bee_cc/flecsale.tar.gz /var/tmp

export OMPI_MCA_btl_vader_single_copy_mechanism=none
export OMPI_MCA_btl=^openib
unset OMPI_MCA_btl_tcp_if_exclude; unset OMPI_MCA_oob_tcp_if_include

#srun -n 5 --mpi=pmi2\
export SLURM_MPI_TYPE="pmi2" # replaces flag
srun -n 5\
  ch-run -w --no-home -b output --cd /mnt/0 /var/tmp/flecsale \
  -- /home/flecsi/flecsale/build/apps/hydro/2d/hydro_2d\
  -m /home/flecsi/flecsale/specializations/data/meshes/2d/square/square_32x32.g

