
"""BEE Cloud class."""

import base64

import beeflow.cloud.provider as provider
import beeflow.cloud.constants as constants


class Node:
    """Node class."""

    def __init__(self, pnode):
        """Node class constructor."""
        self.pnode = pnode

    def get_ext_ip(self):
        """Get the external IP address of the address or None."""
        return self.pnode.get_ext_ip()

    @property
    def ram_per_vcpu(self):
        """Get the amount of RAM per VCPU."""
        return self.pnode.ram_per_vcpu

    @property
    def vcpu_per_node(self):
        """Get the number VPUs per node."""
        return self.pnode.vcpu_per_node


class Cloud:
    """Cloud Class."""

    def __init__(self, provider, priv_key_file=None, node_cnt=1,
                 ram_per_vcpu=2, vcpu_per_node=4):
        """Cloud Class constructor."""
        self.provider = provider
        self.priv_key_file = priv_key_file

    def create_node(self, ram_per_vcpu, vcpu_per_node, ext_ip=None):
        """Create a node."""
        # TODO: Read in the proper pubkey data
        if self.priv_key_file is not None:
            with open(f'{self.priv_key_file}.pub', 'rb') as fp:
                pubkey_data = str(base64.b64encode(fp.read()), encoding='utf-8')

            # TODO: Generate proper startup script
            startup_script = (
                '#!/bin/sh\n'
                f'useradd -m -s /bin/bash {constants.BEE_USER}\n'
                f'echo {constants.BEE_USER}:{constants.BEE_USER} | chpasswd\n'
                f'echo "%{constants.BEE_USER} ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/{constants.BEE_USER}\n'
                f'mkdir -p /home/{constants.BEE_USER}/.ssh\n'
                f'echo {pubkey_data} | base64 -d > /home/{constants.BEE_USER}/.ssh/authorized_keys\n'
                'apt-get -y update\n'
                'apt-get -y install python3 python3-venv python3-pip build-essential\n'
                'curl -O -L https://github.com/hpc/charliecloud/releases/download/v0.22/charliecloud-0.22.tar.gz\n'
                'tar -xvf charliecloud-0.22.tar.gz\n'
                'cd charliecloud-0.22\n'
                './configure --prefix=/usr\n'
                'make\n'
                'make install\n'
            )
        else:
            # Empty start up script
            startup_script = '#!/bin/sh\n'

        pnode = self.provider.create_node(ram_per_vcpu, vcpu_per_node, ext_ip,
                                          startup_script=startup_script)
                                          #keyfile=self.priv_key_file)
        return Node(pnode)

    def wait(self):
        """Wait until all created resources have been set up."""
        self.provider.wait()
