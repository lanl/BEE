"""OpenStack provider module."""
import openstack
from beeflow.common.cloud import provider


class OpenstackProvider(provider.Provider):
    """OpenStack provider class."""

    def __init__(self, stack_name, fake=False, **kwargs):
        """OpenStack provider constructor."""
        self._cloud = openstack.connect()
        self._stack_name = stack_name
        self._kwargs = kwargs
        self._fake = fake

    def create_from_template(self, template_file):
        """Create from a template file."""
        if self._fake:
            return
        self._cloud.create_stack(self._stack_name, template_file=template_file,
                                 wait=True, **self._kwargs)

    def get_ext_ip_addr(self, node_name):
        """Get external IP address of Task Manager node."""
        if self._fake:
            return '1.1.1.1'
        node = self._cloud.get_server(node_name)
        return node.accessIPv4
