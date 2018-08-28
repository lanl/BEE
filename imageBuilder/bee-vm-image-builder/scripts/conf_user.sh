# The UID and GID of albuntu must match host's UID and GID. 
# We need to enable root login, so that we can config UID/GID 
# of albuntu later using bee launcher.
sed -i s/without-password/yes/ /etc/ssh/sshd_config

mkdir /root/.ssh
chmod 777 /root/.ssh

cp /home/ubuntu/tmp/id_rsa /root/.ssh/id_rsa
cp /home/ubuntu/tmp/id_rsa.pub /root/.ssh/id_rsa.pub
cp /home/ubuntu/tmp/authorized_keys /root/.ssh/authorized_keys

#if ["$PACKER_BUILD_NAME" == "qemu"]; then
cp /home/ubuntu/tmp/config /root/.ssh/config
#fi

chown -R root:root /root/.ssh
chmod 700 /root/.ssh
chmod 600 /root/.ssh/id_rsa
chmod 644 /root/.ssh/id_rsa.pub
chmod 644 /root/.ssh/authorized_keys
#if ["$PACKER_BUILD_NAME" == "qemu"]; then
chmod 644 /root/.ssh/config
#fi

# Also config user 'albuntu'.
mkdir /home/ubuntu/.ssh
chmod 777 /home/ubuntu/.ssh

cp /home/ubuntu/tmp/id_rsa /home/ubuntu/.ssh/id_rsa
cp /home/ubuntu/tmp/id_rsa.pub /home/ubuntu/.ssh/id_rsa.pub
cp /home/ubuntu/tmp/authorized_keys /home/ubuntu/.ssh/authorized_keys
#if ["$PACKER_BUILD_NAME" == "qemu"]; then
cp /home/ubuntu/tmp/config /home/ubuntu/.ssh/config
#fi
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh
chmod 600 /home/ubuntu/.ssh/id_rsa
chmod 644 /home/ubuntu/.ssh/id_rsa.pub
chmod 644 /home/ubuntu/.ssh/authorized_keys
#if ["$PACKER_BUILD_NAME" == "qemu"]; then
chmod 644 /home/ubuntu/.ssh/config
#fi

