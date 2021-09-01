#!/bin/sh
# OpenStack BEE install script

# Install Charliecloud
install_charliecloud()
{
    local url=$1
    cd /tmp
    curl -O -L $url || exit 1
    tar -xvf `basename $url`
    local dir=`basename $url | rev | cut -d'.' -f3- | rev`
    cd $dir
    ./configure --prefix=/opt/$dir || exit 1
    make && make install || exit 1
    cat > /etc/profile.d/charliecloud.sh <<EOF
export PATH=/opt/$dir/bin:\$PATH
EOF
}

# Install BEE + dependencies
install_bee()
{
    local auth_token=$1
    local bee_dir=$2
    local conf=$3
    local git_branch=$4
    mkdir -p $bee_dir
    cd $bee_dir
    git clone https://$auth_token:x-oauth-basic@github.com/lanl/BEE_Private.git || exit 1
    cd BEE_Private
    git checkout $git_branch
    python3 -m venv venv
    . venv/bin/activate
    pip install --upgrade pip
    pip install poetry
    poetry update
    poetry install

    # Generate TM init script
    # TODO: May need to start Redis here eventually
    cat >> /bee/tm <<EOF
#!/bin/sh
. /etc/profile
cd /bee/BEE_Private
. ./venv/bin/activate
exec python -m beeflow.task_manager $conf
EOF
    chmod 755 /bee/tm
}

gen_conf()
{
    # local conf=/home/bee/.config/beeflow/bee.conf
    local conf=$1
    local wfm_listen_port=$2
    local tm_listen_port=$3
    cat >> $conf <<EOF
[DEFAULT]
bee_workdir = /home/$USER/.beeflow
workload_scheduler = Simple
[workflow_manager]
listen_port = $wfm_listen_port
log = /home/$USER/.beeflow/logs/wfm.log
[task_manager]
name = dora-tm
listen_port = $tm_listen_port
container_runtime = Charliecloud
log = /home/$USER/.beeflow/logs/tm.log
[charliecloud]
setup = module load charliecloud
image_mntdir = /tmp
chrun_opts = --cd /home/$USER
container_dir = /home/$USER
EOF
}

# Setup Dora specific proxy and nameservers
cat > /etc/profile.d/proxy.sh <<EOF
export https_proxy=$HTTPS_PROXY
export http_proxy=$HTTP_PROXY
export no_proxy=$NO_PROXY
EOF
echo "" > /etc/resolv.conf
for ns in `echo $NAMESERVERS | tr ',' ' '`; do
    printf "nameserver $ns\n" >> /etc/resolv.conf
done
. /etc/profile

# Install general deps
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git curl vim tmux screen gcc make openmpi-bin libopenmpi-dev python3 python3-venv

# Enable user namespaces
/sbin/sysctl kernel.unprivileged_userns_clone=1

install_charliecloud https://github.com/hpc/charliecloud/releases/download/v0.24/charliecloud-0.24.tar.gz
install_bee $GITHUB_PAT /bee /bee/bee.conf $GIT_BRANCH
gen_conf /bee/bee.conf $WFM_LISTEN_PORT $TM_LISTEN_PORT

chown -R $USER:$USER /bee
