#!/bin/sh

# Install necessary libraries
pip install pyro4 --user
pip install boto3 --user

# Remove old files
rm -rf ~/.bee

# Create new directory
mkdir ~/.bee
mkdir ~/.bee/ssh_key
mkdir ~/.bee/vm_imgs
mkdir ~/.bee/tmp

