#!/bin/bash -eux

#  Googling around, this doesn't appear to be necessary [Al]
echo "UseDNS no" >> /etc/ssh/sshd_config
#sed -i s/22/5555/ /etc/ssh/sshd_config
