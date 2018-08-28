#!/bin/sh

ESSENTIAL_PACKAGES="
ntp
nfs-common
nginx
nmap
"

DEV_PACKAGES="
build-essential
curl
git
htop
emacs24
gfortran
nfs-kernel-server
autoconf                                                                                                       automake                                                                                                       libtool        
curl
make
g++
unzip
"

DOCKER_MIGRATION_PACKAGES="
gettext
bison
flex
pkg-config
xmlto
libprotobuf-dev
libprotobuf-c0-dev
protobuf-c-compiler
protobuf-compiler
python-protobuf
libnl-3-dev
libpth-dev
pkg-config
libcap-dev
asciidoc
doxygen
"


#echo $PACKER_BUILD_NAME
#if ["$PACKER_BUILD_NAME" == "qemu"]; then
#    echo "true"
#fi

#if [$PACKER_BUILD_NAME == "qemu"]; then
#    echo "true1"
#fi


#if ["$PACKER_BUILD_NAME" == "qemu"]; then
#    http_proxy=http://proxyout.lanl.gov:8080
#    https_proxy=https://proxyout.lanl.gov:8080
    echo "==> Proxies..."
    echo $http_proxy
    echo $https_proxy


    apt-get -y update

    echo "==> Installing LANL-required essential packages"
    apt-get -y install $ESSENTIAL_PACKAGES
    
    echo "==> Installing LANL-required dev packages"
    apt-get -y install $DEV_PACKAGES

    # Docker Experimental Mode 
    echo "==> Installing Docker Migration required packages"
    apt-get -y install $DOCKER_MIGRATION_PACKAGES

    #Install libnet, this doesn't cannot be installed using apt-get
    cd /home/albuntu
    git clone https://github.com/sam-github/libnet.git
    cd libnet/libnet
    ../Prepare
    ../Build
    sudo make install

    #Install CRIU (Checkpoing/Restore In Userspace) for Docker Migration
    cd /home/albuntu
    git clone https://github.com/xemul/criu.git
    cd criu
    sudo make install
    
#else
    
    
#    sudo apt-get -y update
    
#    echo "==> Installing LANL-required essential packages"
#    sudo apt-get -y install $ESSENTIAL_PACKAGES
    
#    echo "==> Installing LANL-required dev packages"
#    sudo apt-get -y install $DEV_PACKAGES
    
#fi
