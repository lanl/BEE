"""OpenStack provider module."""
import openstack
import beeflow.cloud.provider as provider


class OpenstackProvider(provider.Provider):
    """OpenStack provider class."""

    def __init__(self, stack_name, **kwargs):
        """OpenStack provider constructor."""
        self._cloud = openstack.connect()
        self._stack_name = stack_name
        self._kwargs = kwargs

    def create_from_template(self, template_file):
        """Create from a template file."""
        self.create_stack(self._stack_name, template_file=template_file,
                          wait=True, **self._kwargs)

    def get_ext_ip_addr(self, node_name):
        """Get external IP address of Task Manager node."""
        node = self._cloud.get_server(node_name)
        return node.accessIPv4
