#!/bin/sh
# Install all dependencies for BEE
set -e

sudo apt-get update
sudo apt-get install -y build-essential
sudo apt-get install -y libhttp-parser-dev libjson-c-dev libjwt-dev munge python3 python3-venv \
    curl build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev sqlite3 \
    libssl-dev libsqlite3-dev libreadline-dev libffi-dev libbz2-dev libmunge-dev libdbus-1-dev \
    libpam-dev tcl-dev graphviz libgraphviz-dev libyaml-dev # needed for PyYAML 

# Install Charliecloud
curl -O -L https://gitlab.com/charliecloud/charliecloud/-/archive/v${CHARLIECLOUD_VERSION}/charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
mkdir charliecloud-${CHARLIECLOUD_VERSION}
tar -xvf charliecloud-${CHARLIECLOUD_VERSION}.tar.gz --strip-components=1 -C charliecloud-${CHARLIECLOUD_VERSION}
(cd charliecloud-${CHARLIECLOUD_VERSION}
 ./autogen.sh
 ./configure --prefix=/usr
 make -j4
 sudo make install)

# Install Slurm
SLURM_ARCHIVE="slurm-${SLURM_VERSION}.tar.gz"
SLURM_DIR="slurm-${SLURM_VERSION}"

curl -fL \
  --retry 5 \
  --retry-delay 15 \
  --retry-all-errors \
  --connect-timeout 30 \
  --max-time 300 \
  -o "$SLURM_ARCHIVE" \
  "https://github.com/SchedMD/slurm/archive/refs/tags/${SLURM_TAG}.tar.gz"

mkdir "$SLURM_DIR"

tar -xvf SLURM_ARCHIVE" \
    --strip-components=1 \
    -C "$SLURM_DIR"
(
 cd "$SLURM_DIR"
 ./configure --prefix=/usr --enable-cgroupv2
 grep -i cgroup config.log
 make -j4
 sudo make install
)

# Install Python3
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Set this new Python3 to be the default in the container
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --set python3 /usr/bin/python3.11
