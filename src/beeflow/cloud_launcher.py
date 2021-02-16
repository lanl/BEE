"""BEE Cloud Launcher Script."""

import subprocess
import sys
import time
import os
import base64

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


# TODO: Refactor this code

def generate_private_key(keyfile):
    """Generate the SSH private key."""
    cp = subprocess.run(['ssh-keygen', '-N', '', '-f', keyfile])
    if cp.returncode != 0:
        raise RuntimeError('ssh-keygen failed')


def load_configuration(argv):
    """Load the configuration, setting any defaults."""
    if len(sys.argv) > 2:
        bc = BeeConfig(userconfig=sys.argv[1])
    else:
        bc = BeeConfig()

    # TODO: Check for missing sections
    assert bc.userconfig.has_section('cloud')
    return {
        'bee_workdir': bc.userconfig.get('DEFAULT', 'bee_workdir'),
        'provider': bc.userconfig['cloud'].get('provider', 'Google'),
        'node_count': int(bc.userconfig['cloud'].get('node_count', '2')),
        'ram_per_vcpu': int(bc.userconfig['cloud'].get('ram_per_vcpu', '2')),
        'vcpu_per_node': int(bc.userconfig['cloud'].get('vcpu_per_node', '1')),
        'tm_listen_port': bc.userconfig['task_manager'].get('listen_port', bc.default_tm_port),
        'wfm_listen_port': bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port),
        # Tarball containing the BEE code
        'bee_code': bc.userconfig['cloud'].get('bee_code'),
        # TODO: Get more properties
        # 'provider': bc.userconfig['cloud'].get('provider', 'Google'),
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


def install_and_run_tm(conf, priv_key_file, ip_addr):
    """Install and run the Task Manager."""
    # user_ip = f'{cloud.BEE_USER}@{ip_addr}'
    # opts = ['-i', priv_key_file, '-o', 'StrictHostKeyChecking=no']
    # Copy over the bee code
    """
    cmd = ['scp']
    cmd.extend(opts)
    cmd.extend([conf['bee_code'], f'{user_ip}:~/'])
    subprocess.run(cmd)
    """
    scp(ip_addr, priv_key_file, conf['bee_code'], '~/')

    basename = os.path.basename(conf['bee_code'])
    dirname = basename.split('.')[0]
    # Script to install BEE
    bee_install = [
        '#!/bin/sh\n',
        f'tar -xvf {basename}\n',
        f'cd {dirname}\n',
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

    """
    cmd = ['ssh']
    cmd.extend(opts)
    cmd.extend([user_ip, f'echo {bee_install_b64} | base64 -d > install.sh'])
    subprocess.run(cmd)
    """
    run(ip_addr, priv_key_file, f'echo {bee_install_b64} | base64 -d > install.sh')

    # Run the install script
    """
    cmd = ['ssh']
    cmd.extend(opts)
    cmd.extend([user_ip, 'sh install.sh'])
    subprocess.run(cmd)
    """
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
    """
    cmd = ['scp']
    cmd.extend(opts)
    cmd.extend([tmp_bee_conf, f'{user_ip}:~/.config/beeflow/'])
    subprocess.run(cmd)
    """
    scp(ip_addr, priv_key_file, tmp_bee_conf, '~/.config/beeflow/bee.conf')

    # Now start the Task Manager
    return subprocess.Popen([
        'ssh',
        '-i', priv_key_file,
        f'{cloud.BEE_USER}@{ip_addr}',
        # f'cd {dirname}; . ./venv/bin/activate; beeflow --tm --debug',
        f'cd {dirname}; . ./venv/bin/activate; python -m beeflow.task_manager ~/.config/beeflow/bee.conf',
    ])


def setup(conf):
    """Setup the cloud cluster."""
    # TODO
    provider = cloud.get_provider(conf['provider'])
    priv_key_file = os.path.join(conf['bee_workdir'], 'bee_key')

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
    tm_proc = install_and_run_tm(conf, priv_key_file, ip_addr)
    time.sleep(2)
    if tm_proc.poll() is not None:
        raise RuntimeError('Could not start Remote Task Manager')

    return ip_addr, priv_key_file


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


# TODO
def write_node_file(nodes, node_file):
    """Write a node file containing node names and IP addresses."""
    with open(node_file, 'w') as fp:
        for node in nodes:
            print(node.name, node.get_ext_ip(), file=fp)


# TODO: Add a general connect option to only connect to the remote head node without setup
if __name__ == '__main__':
    # Get configuration values
    conf = load_configuration(sys.argv)

    ip_addr, priv_key_file = setup(conf)
    connect(conf, ip_addr, priv_key_file)
