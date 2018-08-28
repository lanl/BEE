# Add ssh key
mkdir ./ssh_key
cp ~/.bee/ssh_key/* ./ssh_key

# Build and add base image
cp ubuntu1404-qemu-template.json ubuntu1404-qemu.json
sed -i s/UUU/$USER/ ubuntu1404-qemu.json 
packer build -var-file=ubuntu1404-qemu.json ubuntu-qemu.json


