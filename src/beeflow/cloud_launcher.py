"""BEE Cloud Launcher Script."""

import argparse
import base64
import json
import os
import subprocess
import sys
import time

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


# TODO: Refactor this code

def generate_private_key(keyfile):
    """Generate the SSH private key."""
    cp = subprocess.run(['ssh-keygen', '-N', '', '-f', keyfile])
    if cp.returncode != 0:
        raise RuntimeError('ssh-keygen failed')


def load_config():
    """Load the configuration, setting any defaults."""
    parser = argparse.ArgumentParser(description='BEE Cloud Launcher')
    parser.add_argument('config_file', default=None, help='bee.conf file')
    parser.add_argument('--setup', action='store_true',
                        help='set up the remote cloud based on bee.conf')
    parser.add_argument('--tm', action='store_true',
                        help='start the Task Manager on the cloud and connect to it')
    args = parser.parse_args()

    if args.config_file is not None:
        bc = BeeConfig(userconfig=args.config_file)
    else:
        bc = BeeConfig()

    # TODO: Check for missing sections
    assert bc.userconfig.has_section('cloud')
    return {
        # Config file options
        'bee_workdir': bc.userconfig.get('DEFAULT', 'bee_workdir'),
        'cloud_workdir': bc.userconfig.get('cloud', 'cloud_workdir'),
        'provider': bc.userconfig['cloud'].get('provider', 'Google'),
        'node_count': int(bc.userconfig['cloud'].get('node_count', '2')),
        'ram_per_vcpu': int(bc.userconfig['cloud'].get('ram_per_vcpu', '2')),
        'vcpu_per_node': int(bc.userconfig['cloud'].get('vcpu_per_node', '1')),
        'tm_listen_port': bc.userconfig['task_manager'].get('listen_port', bc.default_tm_port),
        'wfm_listen_port': bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port),
        # Tarball containing the BEE code
        'bee_code': bc.userconfig['cloud'].get('bee_code'),

        # Command-line argument options
        'setup': args.setup,
        'tm': args.tm,
    }


def run(ip_addr, priv_key_file, cmd):
    """Run a command on remote machine."""
    cp = subprocess.run([
        'ssh',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        f'{cloud.BEE_USER}@{ip_addr}',
        cmd,
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not run "{cmd}" on the remote machine')


def scp(ip_addr, priv_key_file, src, dst):
    """SCP a file in src to dst on the remote machine."""
    cp = subprocess.run([
        'scp',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        src,
        f'{cloud.BEE_USER}@{ip_addr}:{dst}',
    ])
    if cp.returncode != 0:
        raise RuntimeError(f'Could not copy file "{src}" to "{dst}" on the remote machine')


def install_tm(conf, priv_key_file, ip_addr):
    """Install the Task Manager on the remote machine.

    Returns the directory containing the BEE source code.
    :rtype string
    """
    # user_ip = f'{cloud.BEE_USER}@{ip_addr}'
    # opts = ['-i', priv_key_file, '-o', 'StrictHostKeyChecking=no']
    # Copy over the bee code
    scp(ip_addr, priv_key_file, conf['bee_code'], '~/')

    basename = os.path.basename(conf['bee_code'])
    bee_srcdir = basename.split('.')[0]
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

    run(ip_addr, priv_key_file, f'echo {bee_install_b64} | base64 -d > install.sh')

    # Run the install script
    run(ip_addr, priv_key_file, 'sh install.sh')

    # Make a copy of the bee.conf and make edits to it for running the Task
    # Manager with cloud.BEE_USER
    tmp_bee_conf = f'/tmp/bee_{os.getuid()}.conf'
    with open(os.path.expanduser('~/.config/beeflow/bee.conf')) as fp:
        data = fp.read()
        data = data.replace(conf['bee_workdir'], f'/home/{cloud.BEE_USER}/.beeflow')
        with open(tmp_bee_conf, 'w') as fp:
            fp.write(data)

    # Copy over the modified bee.conf
    scp(ip_addr, priv_key_file, tmp_bee_conf, '~/.config/beeflow/bee.conf')

    return bee_srcdir


def run_tm(ip_addr, priv_key_file, bee_srcdir):
    """Run the Task Manager."""
    # Now start the Task Manager
    return subprocess.Popen([
        'ssh',
        '-i', priv_key_file,
        '-o', 'StrictHostKeyChecking=no',
        f'{cloud.BEE_USER}@{ip_addr}',
        # f'cd {dirname}; . ./venv/bin/activate; beeflow --tm --debug',
        f'cd {bee_srcdir}; . ./venv/bin/activate; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
    ])


def setup(conf, priv_key_file):
    """Setup the cloud cluster.

    Returns the IP address of the cluster head node and the directory of the
    BEE source code on the head node.
    :rtype tuple (str, str)
    """
    provider = cloud.get_provider(conf['provider'])

    # Generate the private key if it doesn't exist yet
    if (not os.path.exists(priv_key_file)
            or not os.path.exists(f'{priv_key_file}.pub')):
        generate_private_key(priv_key_file)

    # Set up the Cloud
    c = cloud.Cloud(provider, priv_key_file=priv_key_file)

    # Create the head node
    print('Creating head node')
    head_node = c.create_node(ram_per_vcpu=conf['ram_per_vcpu'],
                              vcpu_per_node=conf['vcpu_per_node'], ext_ip=True)
    # Create the worker nodes
    nodes = []
    for i in range(conf['node_count']):
        print('Creating node', i)
        nodes.append(c.create_node(ram_per_vcpu=2, vcpu_per_node=2,
                                   ext_ip=False))

    # Wait for set up to complete
    print('Waiting for cloud setup...')
    c.wait()
    ip_addr = head_node.get_ext_ip()

    # Copy over the BEE code and install it
    bee_srcdir = install_tm(conf, priv_key_file, ip_addr)

    return ip_addr, bee_srcdir


def connect(conf, ip_addr, priv_key_file):
    """Connect to the remote head node."""
    # TODO
    # Open SSH Tunnel or VPN to the remote Task Manager
    tm_listen_port = conf['tm_listen_port']
    wfm_listen_port = conf['wfm_listen_port']
    print('Setting up SSH tunnel to head node')
    tun_proc = subprocess.Popen([
        'ssh',
        f'{cloud.BEE_USER}@{ip_addr}',
        '-i', priv_key_file,
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
    time.sleep(2)
    if tun_proc.poll() is not None:
        raise RuntimeError('Could not set up SSH Connection')

    # Wait on the SSH tunnel process
    tun_proc.wait()


# TODO: Use a more object oriented/encapsulated design here

# TODO: Add a general connect option to only connect to the remote head node without setup
if __name__ == '__main__':
    # Get configuration values
    conf = load_config()
    priv_key_file = os.path.join(conf['bee_workdir'], 'bee_key')

    # File to store temporary cloud information
    cloud_info_file = os.path.join(conf['bee_workdir'], 'cloud-info.json')
    if conf['setup']:
        # Set up the cloud
        ip_addr, bee_srcdir = setup(conf, priv_key_file)
        with open(cloud_info_file, 'w') as fp:
            json.dump({
                'ext_ip_addr': ip_addr,
                'bee_srcdir': bee_srcdir,
            }, fp=fp, indent=4)
        print(f'Cloud setup should be complete. You should check by logging into the remote head node ({cloud.BEE_USER}@{ip_addr}).')
    else:
        # Cloud should already be set up, so get info from the cloud info file
        try:
            with open(cloud_info_file) as fp:
                data = json.load(fp)
        except FileNotFoundError:
            print('Cloud info file is missing. You need to run setup before you can start the Task Manager',
                  file=sys.stderr)
            sys.exit(1)
        ip_addr = data['ext_ip_addr']
        bee_srcdir = data['bee_srcdir']

    if conf['tm']:
        # Launch the task manager
        print('Launching the Remote Task Manager')
        tm_proc = run_tm(ip_addr, priv_key_file, bee_srcdir)

        time.sleep(2)
        if tm_proc.poll() is not None:
            raise RuntimeError('Could not start Remote Task Manager')

        # Set up the connection
        connect(conf, ip_addr, priv_key_file)
