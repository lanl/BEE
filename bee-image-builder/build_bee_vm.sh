# Add ssh key
cp ssh_key/id_rsa ~/.bee/ssh_key/id_rsa
chmod 600 ~/.bee/ssh_key/id_rsa

# Build and add base image
cp ubuntu1404-qemu-template.json ubuntu1404-qemu.json
sed -i s/UUU/$USER/ ubuntu1404-qemu.json 
packer build -var-file=ubuntu1404-qemu.json ubuntu-qemu.json


