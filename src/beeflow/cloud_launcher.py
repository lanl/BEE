
"""BEE Cloud Installer Script."""

import argparse
import base64
import configparser
import os
import subprocess
import sys
import tempfile
import time

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


class CloudLauncherError(Exception):
    """Cloud launcher error class."""

    def __init__(self, msg):
        """Cloud launcher error constructor."""
        self.msg = msg


def generate_private_key(keyfile):
    """Generate the SSH private key."""
    cp = subprocess.run(['ssh-keygen', '-N', '', '-f', keyfile])
    if cp.returncode != 0:
        raise RuntimeError('ssh-keygen failed')


def run(bee_user, ip_addr, priv_key_file, cmd):
    """Run a command on remote machine."""
    cp = subprocess.run([
        'ssh',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        f'{bee_user}@{ip_addr}',
        cmd,
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not run "{cmd}" on the remote machine')


def scp(bee_user, ip_addr, priv_key_file, src, dst):
    """SCP a file in src to dst on the remote machine."""
    cp = subprocess.run([
        'scp',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        src,
        f'{bee_user}@{ip_addr}:{dst}',
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not copy file "{src}" to "{dst}" on the remote machine')


def setup(provider, head_node, bee_user, private_key_file):
    """Setup the cloud cluster.

    Returns the IP address of the cluster head node and the directory of the
    BEE source code on the head node.
    :rtype tuple (str, str)
    """
    # Generate the private key if it doesn't exist yet
    if not os.path.exists(private_key_file):
        generate_private_key(private_key_file)

    # Read in the pub key data
    try:
        with open(f'{private_key_file}.pub', 'rb') as fp:
            pubkey_data = str(base64.b64encode(fp.read()), encoding='utf-8')
    except FileNotFoundError:
        raise CloudLauncherError('Could not find public key from the specified private key file')

    # TODO: Generate startup script based on distribution
    startup_script = (
        '#!/bin/sh\n'
        f'useradd -m -s /bin/bash {bee_user}\n'
        f'echo {bee_user}:{bee_user} | chpasswd\n'
        f'echo "%{bee_user} ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/{bee_user}\n'
        f'mkdir -p /home/{bee_user}/.ssh\n'
        f'echo {pubkey_data} | base64 -d > /home/{bee_user}/.ssh/authorized_keys\n'
        'apt-get -y update\n'
        'apt-get -y install python3 python3-venv python3-pip build-essential\n'
        'curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.22/charliecloud-0.22.tar.gz\n'
        'tar -xvf charliecloud-0.22.tar.gz\n'
        'cd charliecloud-0.22\n'
        './configure --prefix=/usr\n'
        'make\n'
        'make install\n'
        '# Enable user+mount namespaces\n'
        'sysctl kernel.unprivileged_userns_clone=1\n'
    )

    # TODO: Allow for node type specification
    # Create the head node
    print('Creating head node')
    provider.create_node(head_node, startup_script=startup_script, ext_ip=True)

    # TODO: Create worker nodes (if requested)

    # Wait for set up
    print('Waiting for cloud setup')
    provider.wait()

    # TODO: Setup interconnect between the nodes


def srcdir(src):
    """Get the source directory for the untarred source."""
    basename = os.path.basename(src)
    return basename.split('.')[0]


def install_tm(provider, head_node, private_key_file, bee_code, config_file, bee_user):
    """Install the Task Manager on the remote machine.

    Returns the directory containing the BEE source code.
    :rtype string
    """
    ip_addr = provider.get_ext_ip_addr(head_node)

    # Copy over the bee code
    if bee_code is None:
        raise cloud.CloudError('`bee_code` option is required for installing the TM')
    scp(bee_user, ip_addr, private_key_file, bee_code, '~/')
    # Determine the bee code file and source directory
    basename = os.path.basename(bee_code)
    bee_srcdir = srcdir(bee_code)

    # Script to install BEE
    bee_install = [
        '#!/bin/sh\n',
        f'tar -xvf {basename}\n',
        f'cd {bee_srcdir}\n',
        'python3 -m venv venv\n',
        '. ./venv/bin/activate\n',
        'pip install --upgrade pip\n',
        'pip install poetry\n',
        'poetry install\n',
        # Also create the config directory
        'mkdir -p ~/.config/beeflow\n',
    ]
    bee_install = ''.join(bee_install)
    # Send the script as base64 over to the machine
    bee_install = bytes(bee_install, encoding='utf-8')
    bee_install_b64 = str(base64.b64encode(bee_install), encoding='utf-8')

    run(bee_user, ip_addr, private_key_file, f'echo {bee_install_b64} | base64 -d > install.sh')

    # Run the install script
    run(bee_user, ip_addr, private_key_file, 'sh install.sh')

    # Modify a copy of the configuration file for the remote TM
    fd, tmp_bee_conf = tempfile.mkstemp()
    cfg = configparser.ConfigParser()
    cfg.read(config_file)
    cfg.set('DEFAULT', 'bee_workdir', f'/home/{bee_user}/.beeflow')
    cfg.set('task_manager', 'log', f'/home/{bee_user}/tm.log')
    with open(tmp_bee_conf, 'w') as fp:
        cfg.write(fp)
    # Copy over the modified bee.conf
    scp(bee_user, ip_addr, private_key_file, tmp_bee_conf, '~/.config/beeflow/bee.conf')


def tm(provider, private_key_file, head_node, bee_user, bee_code, tm_listen_port, wfm_listen_port):
    """Start the Task Manager on the remote head node."""
    print('Launching the Remote Task Manager')
    bee_srcdir = srcdir(bee_code)
    ip_addr = provider.get_ext_ip_addr(head_node)

    # Now start the Task Manager
    tm_proc = subprocess.Popen([
        'ssh',
        '-i', private_key_file,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=8',
        f'{bee_user}@{ip_addr}',
        f'cd ~/{bee_srcdir}; . ./venv/bin/activate; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
    ])
    time.sleep(10)
    if tm_proc.poll() is not None:
        raise RuntimeError('Failed to launch the Remote Task Manager')

    # Set up the connection
    try:
        tun_proc = subprocess.run([
            'ssh',
            f'{bee_user}@{ip_addr}',
            '-i', private_key_file,
            # The TM is listening on the remote machine
            '-L', f'{tm_listen_port}:localhost:{tm_listen_port}',
            # The WFM is listening on this machine
            '-R', f'{wfm_listen_port}:localhost:{wfm_listen_port}',
            '-N',
            '-o', 'ExitOnForwardFailure=yes',
            '-o', 'StrictHostKeyChecking=no',
            # Required in order to allow port forwarding
            '-o', 'UserKnownHostsFile=/dev/null',
        ])
    finally:
        print('Killing the task manager')
        tm_proc.kill()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='BEE Cloud Installer')
    parser.add_argument('config_file', help='bee.conf file')
    parser.add_argument('--setup-cloud', action='store_true', help='set up the remote cloud')
    parser.add_argument('--install-tm', action='store_true', help='install the TM')
    parser.add_argument('--tm', action='store_true', help='start the TM')
    args = parser.parse_args()

    # Get all configuration information
    bc = BeeConfig(userconfig=args.config_file, workload_scheduler='Simple')
    if not bc.userconfig.has_section('cloud'):
        print('Missing [cloud] section in the bee.conf file', file=sys.stderr)
        sys.exit(1)
    bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
    head_node = bc.userconfig['cloud'].get('head_node', 'bee-head-node')
    private_key_file = bc.userconfig['cloud'].get('private_key_file',
                                                  os.path.join(bee_workdir, 'bee_key'))
    bee_user = bc.userconfig['cloud'].get('bee_user', cloud.BEE_USER)
    bee_code = bc.userconfig['cloud'].get('bee_code', None)
    # Get the component ports for forwarding connections
    wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port')
    tm_listen_port = bc.userconfig['task_manager'].get('listen_port')
    # Get the cloud provider configuration
    provider = bc.userconfig['cloud'].get('provider', None)
    if provider is None:
        raise cloud.CloudError('No `provider` option was specified. This is required for Cloud setup.')
    provider_config = f'cloud.{provider}'
    if not bc.userconfig.has_section(provider_config):
        raise cloud.CloudError('Missing provider configuration file')
    # Now get the provider interface
    kwargs = dict(bc.userconfig[provider_config])
    provider = cloud.get_provider(provider, **kwargs)

    if args.setup_cloud:
        setup(provider=provider, head_node=head_node, bee_user=bee_user,
              private_key_file=private_key_file)
    if args.install_tm:
        install_tm(provider=provider, head_node=head_node, private_key_file=private_key_file,
                   bee_code=bee_code, config_file=args.config_file, bee_user=bee_user)
    if args.tm:
        tm(provider=provider, private_key_file=private_key_file, head_node=head_node,
           bee_user=bee_user, bee_code=bee_code,
           wfm_listen_port=wfm_listen_port, tm_listen_port=tm_listen_port)
