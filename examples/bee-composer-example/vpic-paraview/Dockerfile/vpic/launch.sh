#!/bin/bash

echo "Sleeping 5 on master"

sleep 5

echo "Starting vpic on master"

# make the run directory belong to vpic
cp -r /home/beeuser/* /mnt/docker_share
mkdir -p /mnt/docker_share/vpic.bin

# run the vpic code  on master
/mnt/docker_share/runvpic.sh 

