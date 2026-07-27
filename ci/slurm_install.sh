#!/bin/sh
# Install Slurm for BEE
set -e

curl -O -L https://download.schedmd.com/slurm/slurm-${SLURM_VERSION}.tar.bz2
tar -xvf slurm-${SLURM_VERSION}.tar.bz2
(cd slurm-${SLURM_VERSION}
 ./configure --prefix=$GITHUB_WORKSPACE/slurm --enable-cgroupv2
 grep -i cgroup config.log
 make -j4
 sudo make install)
