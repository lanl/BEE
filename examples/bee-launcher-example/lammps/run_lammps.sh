#!/bin/bash
#cat /lammps/examples/melt/in.melt
#IN="/mnt/docker_share/in.melt"  
DIR_SHARE=/mnt/docker_share


#OUT_TXT="example"
#IN="/lammps/examples/melt/in.melt" 
OUT_TXT="500"
IN="$DIR_SHARE/in.melt"  

DIR_OUT="$DIR_SHARE/$OUT_TXT"

PROG="/lammps/src/lmp_mpi"
FLAGS="--allow-run-as-root --mca btl_tcp_if_include eth0 --hostfile /root/hostfile"
mkdir -p $DIR_SHARE/$OUT_TXT


#for icores in 1 2 4 8 16
for icores in 32
do
  echo "----------------------------------------------------------" 
  echo "Running on $icores cores using input from $IN " 
  echo "Output in $DIR_OUT "
  mpirun $FLAGS -np $icores $PROG -in $IN 2>&1 | tee $DIR_OUT/n$icores-$OUT_TXT-melt.out
done

date
