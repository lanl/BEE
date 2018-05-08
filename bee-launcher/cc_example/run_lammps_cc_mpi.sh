#!/bin/bash

# parallel run of lammps for BEE Charliecloud launcher
ch-run \
 -b /home/pagrubel/share/bee_cc_share \
 -b /home/pagrubel/share/bee_cc_share/out \
 /var/tmp/lammps_example \
 -- /lammps/src/lmp_mpi \
 -in /mnt/0/in50.melt -log /mnt/1/lammps.log # has larger region 50 steps

# -in /lammps/examples/melt/in.melt -log /mnt/1/lammps.log

# Specify the nodes to be used and mapping in beefile

