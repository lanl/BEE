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
    
#else
    
    
#    sudo apt-get -y update
    
#    echo "==> Installing LANL-required essential packages"
#    sudo apt-get -y install $ESSENTIAL_PACKAGES
    
#    echo "==> Installing LANL-required dev packages"
#    sudo apt-get -y install $DEV_PACKAGES
    
#fi
