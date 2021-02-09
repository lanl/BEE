"""BEE Cloud class."""
import beeflow.cloud.provider as provider


class Node:
    """Node class."""

    def __init__(self, pnode):
        """Node class constructor."""
        # TODO
        self.pnode = pnode

    def get_ext_ip(self):
        """Get the external IP address of the address or None."""
        # TODO
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
        # TODO
        self.provider = provider

    def create_node(self, ram_per_vcpu, vcpu_per_node, ext_ip=None):
        """Create a node."""
        pnode = self.provider.create_node(ram_per_vcpu, vcpu_per_node, ext_ip)
        return Node(pnode)

    def wait(self):
        """Wait until all created resources have been set up."""
        self.provider.wait()
