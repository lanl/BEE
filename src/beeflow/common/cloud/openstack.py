"""OpenStack provider module."""
import openstack
from beeflow.common.cloud import provider
from beeflow.common.cloud.cloud import CloudError


class OpenstackProvider(provider.Provider):
    """OpenStack provider class."""

    def __init__(self, stack_name, **_kwargs):
        """Construct a new OpenStack provider class."""
        self._cloud = openstack.connect()
        self._stack_name = stack_name

    def get_ext_ip_addr(self, node_name):
        """Get external IP address of Task Manager node."""
        node = self._cloud.get_server(node_name)
        if node is None:
            raise CloudError('Cannot retrieve node/IP information. Is `node_name` set correctly?')
        return node.accessIPv4

    def setup_cloud(self, config):
        """Set up the cloud based on config data."""
        # Just write out the template to the pwd for right now
        template_file = './openstack.yaml'
        with open(template_file, 'w', encoding='utf-8') as fp:
            fp.write(config)
        self._cloud.create_stack(self._stack_name, template_file=template_file, wait=True)
