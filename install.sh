#!/bin/sh

# Install necessary libraries
pip install pyro4 --user
pip install boto3 --user
pip install termcolor --user
pip install tabulate --user
pip install pexpect --user


# Remove old files
rm -rf ~/.bee

# Create new directory
mkdir ~/.bee
mkdir ~/.bee/ssh_key
mkdir ~/.bee/vm_imgs
mkdir ~/.bee/tmp

# Create SSH Key
ssh-keygen -t rsa -f ~/.bee/ssh_key/id_rsa -q -P ""
