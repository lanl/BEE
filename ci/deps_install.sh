#!/bin/sh
# Install all dependencies for BEE
set -e

sudo apt-get update
sudo apt-get install -y slurmctld slurmd slurmrestd munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev \
    libmunge-dev \
    libyaml-dev # needed for PyYAML

# Install most recent Charliecloud
curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.34/charliecloud-0.34.tar.gz
tar -xvf charliecloud-0.34.tar.gz
(cd charliecloud-0.34
 ./configure --prefix=/usr
 make
 sudo make install)

# Install Python3
sudo apt-get install -y software-properties-common
sudo apt-get install -y python3 python3-dev python3-venv
