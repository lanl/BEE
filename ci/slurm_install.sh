#!/bin/sh
# Install Slurm for BEE
set -e

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

tar -xzvf "$SLURM_ARCHIVE" \
    --strip-components=1 \
    -C "$SLURM_DIR"
(
 cd "$SLURM_DIR"
 ./configure --prefix=$GITHUB_WORKSPACE/slurm --enable-cgroupv2
 grep -i cgroup config.log
 make -j4
 sudo make install
)
