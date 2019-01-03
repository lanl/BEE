# Install Docker
# Ubuntu 14.04
# https://docs.docker.com/install/linux/docker-ce/ubuntu

#apt-get -y install apt-transport-https ca-certificates
#apt-key adv \
#     --keyserver hkp://ha.pool.sks-keyservers.net:80 \
#     --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
#echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | tee /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

apt-key fingerprint 0EBFCD88

add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

apt-get update

apt-get install -y linux-image-extra-$(uname -r) linux-image-extra-virtual
#apt-get -y install docker-engine
apt-get install -y docker-ce

echo "export http_proxy="$http_proxy >> /etc/default/docker
echo "export https_proxy="$https_proxy >> /etc/default/docker

# Docker Experimental Mode
echo "DOCKER_OPTS=\"--experimental\"" >> /etc/default/docker

#  Should not do this in the wild! But, we'er in a VM, the whole purpose of
#  which is to deal with this docker as root security hole.
# groupadd docker
usermod -aG docker $docker_user
# service docker start


