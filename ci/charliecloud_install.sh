#!/bin/sh
# Install Charliecloud for BEE
set -e

curl -O -L https://gitlab.com/charliecloud/charliecloud/-/archive/v${CHARLIECLOUD_VERSION}/charliecloud-${CHARLIECLOUD_VERSION}.tar.gz
mkdir charliecloud-${CHARLIECLOUD_VERSION}
tar -xvf charliecloud-${CHARLIECLOUD_VERSION}.tar.gz --strip-components=1 -C charliecloud-${CHARLIECLOUD_VERSION}
(cd charliecloud-${CHARLIECLOUD_VERSION}
 ./autogen.sh
 ./configure --prefix=$GITHUB_WORKSPACE/charliecloud
 make -j4
 sudo make install)
