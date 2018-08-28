#!/bin/sh   

mkdir /home/ubuntu/vmshare

#if ["$PACKER_BUILD_NAME" == "qemu"]; then
    #origial way(using nfs)
    echo "/home/ubuntu/vmshare *(sync,rw,no_root_squash)" >> /etc/exports
#fi
