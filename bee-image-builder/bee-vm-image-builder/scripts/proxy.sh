#!/bin/sh
echo $PACKER_BUILD_NAME

echo "Acquire::http::Proxy \"$http_proxy\";" >> /etc/apt/apt.conf
echo "Acquire::https::Proxy \"$https_proxy\";" >> /etc/apt/apt.conf
    
git config --global http.proxy $http_proxy
git config --global https.proxy $https_proxy

