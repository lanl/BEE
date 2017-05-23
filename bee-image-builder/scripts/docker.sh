# Install Docker
apt-get -y install apt-transport-https ca-certificates
apt-key adv \
     --keyserver hkp://ha.pool.sks-keyservers.net:80 \
     --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | tee /etc/apt/sources.list.d/docker.list
apt-get -y update
apt-get -y install linux-image-extra-$(uname -r) linux-image-extra-virtual
apt-get -y update
apt-get -y install docker-engine
echo "export http_proxy="$http_proxy >> /etc/default/docker
echo "export https_proxy="$https_proxy >> /etc/default/docker
#  Should not do this in the wild! But, we'er in a VM, the whole purpose of
#  which is to deal with this docker as root security hole.
# groupadd docker
usermod -aG docker $docker_user
# service docker start

