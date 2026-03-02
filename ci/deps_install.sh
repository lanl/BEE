#!/bin/sh
# Install all dependencies for BEE
set -e

sudo apt-get update
sudo apt-get install -y libhttp-parser-dev libjson-c-dev libjwt-dev munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev sqlite3 \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev libmunge-dev \
    libyaml-dev # needed for PyYAML 

sudo apt-get install -y graphviz libgraphviz-dev

# Install most recent Charliecloud
curl -O -L https://github.com/hpc/charliecloud/releases/download/v${CHARLIECLOUD_VERSION}/charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
tar -xvf charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
(cd charliecloud-${CHARLIECLOUD_VERSION}
 ./configure --prefix=/usr
 make -j4
 sudo make install)

# Install Slurm
curl -O -L https://download.schedmd.com/slurm/slurm-${SLURM_VERSION}.tar.bz2
tar -xvf slurm-${SLURM_VERSION}.tar.bz2
(cd slurm-${SLURM_VERSION}
 ./configure --prefix=/usr
 make -j4
 sudo make install)

# Install Python3
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Set this new Python3 to be the default in the container
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --set python3 /usr/bin/python3.11
