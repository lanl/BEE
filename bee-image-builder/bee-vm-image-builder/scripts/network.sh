#!/bin/sh

#if ["$PACKER_BUILD_NAME" == "qemu"]; then

# Disable udev persistent net rules
rm /etc/udev/rules.d/70-persistent-net.rules
mkdir /etc/udev/rules.d/70-persistent-net.rules
rm /lib/udev/rules.d/75-persistent-net-generator.rules
rm -rf /dev/.udev/ /var/lib/dhcp3/*
echo "pre-up sleep 2" >> /etc/network/interfaces

# Disable DNS reverse lookup
echo "UseDNS no" >> /etc/ssh/sshd_config


# Setup network
# Add script to let VM setup virtual NIC
cp /home/ubuntu/tmp/rc.local /etc/rc.local
cp /home/ubuntu/tmp/interfaces /etc/network/interfaces

chmod 755 /etc/rc.local
chmod 755 /etc/network/interfaces

#fi
