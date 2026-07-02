#!/bin/sh
# Build and Configure Charliecloud and Slurm 
set -e 

# Build and Configure Charliecloud
curl -O -L https://gitlab.com/charliecloud/charliecloud/-/archive/v${CHARLIECLOUD_VERSION}/charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
mkdir charliecloud-${CHARLIECLOUD_VERSION}
tar -xvf charliecloud-${CHARLIECLOUD_VERSION}.tar.gz --strip-components=1 -C charliecloud-${CHARLIECLOUD_VERSION}
(cd charliecloud-${CHARLIECLOUD_VERSION}
 ./autogen.sh
 ./configure
 make -j4)

# Build and Configure Slurm
curl -O -L https://download.schedmd.com/slurm/slurm-${SLURM_VERSION}.tar.bz2
tar -xvf slurm-${SLURM_VERSION}.tar.bz2
(cd slurm-${SLURM_VERSION}
 ./configure --enable-cgroupv2
 grep -i cgroup config.log
 make -j4)
