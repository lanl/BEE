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
cp ./travis_ci/id_rsa ~/.bee/ssh_key/id_rsa
chmod 600 ~/.bee/ssh_key/id_rsa

# Add authorized_keys
cp ./travis_ci/id_rsa.pub ~/.bee/ssh_key/id_rsa.pub
cat ~/.bee/ssh_key/id_rsa.pub >> ~/.bee/ssh_key/authorized_keys

# Setup SSH config
echo "Host *" >> ~/.bee/ssh_key/config
echo "     Port 22" >> ~/.bee/ssh_key/config
echo "     StrictHostKeyChecking no" >> ~/.bee/ssh_key/config
echo "     UserKnownHostsFile=/dev/null" >> ~/.bee/ssh_key/config

export PATH=$(pwd)/bee-launcher:$PATH
echo $PATH