#!/bin/sh
# Install all dependencies for BEE
set -e

sudo apt-get update
sudo apt-get install -y slurmctld slurmd slurmrestd munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev \
    libmunge-dev \
    libyaml-dev # needed for PyYAML 

sudo apt-get install -y graphviz libgraphviz-dev

# Install most recent Charliecloud
curl -O -L https://github.com/hpc/charliecloud/releases/download/v${CHARLIECLOUD_VERSION}/charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
tar -xvf charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
(cd charliecloud-${CHARLIECLOUD_VERSION}
 ./configure --prefix=/usr
 make
 sudo make install)

# Install Python3
sudo apt-get install -y software-properties-common
sudo apt-get install -y python3 python3-dev python3-venv
