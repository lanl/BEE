#!/bin/bash
mkdir -p out

# parallel run of lammps for BEE Charliecloud launcher
ch-run \
 -b out \
 /var/tmp/lammps_example \
 -- /lammps/src/lmp_mpi \
 -in /lammps/examples/melt/in.melt -log /mnt/0/lammps_mpi_1.log # has larger region 50 steps

# Specify the nodes to be used and mapping in beefile

