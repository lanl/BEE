"""BEE Cloud Launcher Script."""

import subprocess
import time

import beeflow.cloud as cloud


if __name__ == '__main__':
    # Get configuration values
    # TODO
    # Set up the Cloud
    provider = cloud.get_provider('Google')
    priv_key_file = '/home/jaket/bee_key'
    c = cloud.Cloud(provider, priv_key_file=priv_key_file)
    nodes = []
    for i in range(3):
        nodes.extend(c.create_node(ram_per_vcpu=2, vcpu_per_node=2,
                                   ext_ip=True))
    # TODO: Print out information about the nodes
    # Wait for set up to complete
    c.wait()
    ip_addr = c.head_node_ip
    # Open SSH Tunnel or VPN to the remote Task Manager
    proc = subprocess.Popen([
        'ssh',
        'bee@172.16.1.1',
        '-L', f'{port}:localhost:{port}',
        '-N',
        '-o', 'ExitOnForwardFailure=yes'
    ])
    time.sleep(2)
    if proc.poll() is not None:
        raise RuntimeError('Could not set up SSH Connection')

    # Wait on the SSH tunnel process
    proc.wait()
