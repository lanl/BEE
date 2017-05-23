#!/bin/sh
echo $PACKER_BUILD_NAME
#if ["$PACKER_BUILD_NAME" == "qemu"]; then

    #To make apt-get work in VM.
    #echo "Acquire::http::Proxy \"http://proxyout.lanl.gov:8080\";" >> /etc/apt/apt.conf
    #echo "Acquire::https::Proxy \"http://proxyout.lanl.gov:8080\";" >> /etc/apt/apt.conf
    echo "Acquire::http::Proxy \"$http_proxy\";" >> /etc/apt/apt.conf
    echo "Acquire::https::Proxy \"$https_proxy\";" >> /etc/apt/apt.conf
    #when use non-interactive login to execute git clone, proxy must be set before
    #git config --global http.proxy http://proxyout.lanl.gov:8080
    #git config --global https.proxy http://proxyout.lanl.gov:8080
    
    git config --global http.proxy $http_proxy
    git config --global https.proxy $https_proxy

#fi
