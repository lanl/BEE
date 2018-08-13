#!/bin/bash

# mpirun -np 32 ch-run \ #if you want to specify using all cpus (default)
# or any flag to specify hosts, mapping by node etc.

# The following need to happen
# the modules need to be loaded before the allocation in the same window as
# bee_orc_ctl.py is run and the allocation needs to be done in that window
# or a path set to openmpi and charliecloud
mkdir -p out
mpirun ch-run \
	-b out \
	/var/tmp/lammps_example \
	-- /lammps/src/lmp_mpi \
	-in /lammps/examples/melt/in.melt -log /mnt/0/lammps_gen.log # has larger region 50 steps
