"""BEE Cloud Launcher Script."""

import subprocess
import sys
import time
import os

import beeflow.cloud as cloud
from beeflow.common.config_driver import BeeConfig


BEE_USER = 'bee'


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
        'tm_listen_port': bc.userconfig.get('task_manager', 'listen_port'),
        'wfm_listen_port': bc.userconfig['workflow_manager'].get('listen_port', bc.default_wfm_port),
        # TODO: Get more properties
        # 'provider': bc.userconfig['cloud'].get('provider', 'Google'),
    }


if __name__ == '__main__':
    # Get configuration values
    conf = load_configuration(sys.argv)
    provider = cloud.get_provider(conf['provider'])
    priv_key_file = os.path.join(conf['bee_workdir'], 'bee_key')

    if not os.path.exists(priv_key_file) or not os.path.exists(f'{priv_key_file}.pub'):
        generate_private_key(priv_key_file)

    # Set up the Cloud
    c = cloud.Cloud(provider, priv_key_file=priv_key_file)

    # Create the head node
    head_node = c.create_node(ram_per_vcpu=2, vcpu_per_node=2, ext_ip=True)
    # Create the worker nodes
    nodes = []
    for i in range(3):
        nodes.append(c.create_node(ram_per_vcpu=2, vcpu_per_node=2,
                                   ext_ip=False))

    # Wait for set up to complete
    c.wait()
    ip_addr = head_node.get_ext_ip()

    # Open SSH Tunnel or VPN to the remote Task Manager
    tm_listen_port = conf['tm_listen_port']
    wfm_listen_port = conf['wfm_listen_port']
    proc = subprocess.Popen([
        'ssh',
        f'{cloud.BEE_USER}@{ip_addr}',
        '-i', priv_key_file,
        # The TM is listening on the remote machine
        '-L', f'{tm_listen_port}:localhost:{tm_listen_port}',
        # The WFM is listening on this machine
        '-R', f'{wfm_listen_port}:localhost:{wfm_listen_port}',
        '-N',
        '-o', 'ExitOnForwardFailure=yes,StrictHostKeyChecking=no',
    ])
    time.sleep(2)
    if proc.poll() is not None:
        raise RuntimeError('Could not set up SSH Connection')

    # Wait on the SSH tunnel process
    proc.wait()
