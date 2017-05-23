# Remove old files
rm -rf ~/.bee

# Create new directory
mkdir ~/.bee
mkdir ~/.bee/ssh_key
mkdir ~/.bee/vm_imgs
mkdir ~/.bee/tmp

# Add ssh key
cp ssh_key/id_rsa ~/.bee/ssh_key/id_rsa

# Build and add base image
cp ubuntu1404-qemu-template.json ubuntu1404-qemu.json
sed -i s/UUU/$USER/ ubuntu1404-qemu.json 
packer build -var-file=ubuntu1404-qemu.json ubuntu-qemu.json

# Create data img
qemu-img create -f ~/.bee/base_img/qcow2 base_data_img 20G 
