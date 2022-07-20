#!/bin/sh
# Install all dependencies for BEE
sudo apt-get update
sudo apt-get install -y slurmctld slurmd slurmrestd munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev

# Install most recent Charliecloud
curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.27/charliecloud-0.27.tar.gz
tar -xvf charliecloud-0.27.tar.gz
(cd charliecloud-0.27
 ./configure --prefix=/usr
 make
 sudo make install)

# Use a PPA to install Python3.8
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.8 python3.8-dev python3.8-venv
