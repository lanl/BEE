#!/bin/sh

# Install necessary libraries
pip install pyro4 --user
pip install boto3 --user
pip install termcolor --user
pip install tabulate --user
pip install pexpect --user
pip install python-openstackclient --user
pip install python-heatclient --user
pip install python-neutronclient --user


# Remove old files
rm -rf ~/.bee

# Create new directory
mkdir ~/.bee
mkdir ~/.bee/ssh_key
mkdir ~/.bee/vm_imgs
mkdir ~/.bee/tmp


# Create SSH Key
ssh-keygen -t rsa -f ~/.bee/ssh_key/id_rsa -q -P ""
chmod 600 ~/.bee/ssh_key/id_rsa

# Add authorized_keys
cat ~/.bee/ssh_key/id_rsa.pub >> ~/.bee/ssh_key/authorized_keys

# Setup SSH config
echo "Host *" >> ~/.bee/ssh_key/config
echo "     Port 22" >> ~/.bee/ssh_key/config
echo "     StrictHostKeyChecking no" >> ~/.bee/ssh_key/config
echo "     UserKnownHostsFile=/dev/null" >> ~/.bee/ssh_key/config

# Create bee_conf.json
echo "{\"pyro4-ns-port\": 12345}" >> ~/.bee/bee_conf.json

# Adding bee-launcher to path
export PATH=$PATH:"$PWD"/bee-launcher
