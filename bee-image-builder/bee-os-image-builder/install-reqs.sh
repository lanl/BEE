#!/bin/bash

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

### OS-specific installs

function centos_reqs() {
  yum install -y epel-release
  yum install -y qemu-img python-pip kpartx #python-virtualenv
}

function ubuntu_reqs() {
  apt-get -qq install -y qemu-utils python-pip kpartx
}

source /etc/os-release
if [[ $ID = 'ubuntu' ]]; then
  ubuntu_reqs
else
  if [[ $ID = 'centos' ]]; then
    centos_reqs
  else
    echo 'Unknown distribution (not CentOS or Ubuntu?), aborting.'
    exit 1
  fi
fi

### Generic installs

# pip install --upgrade pip
# this is a bit dirty, you should probably use a virtualenv
pip install diskimage-builder
