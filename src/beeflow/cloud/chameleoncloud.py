"""Chameleon provider code."""

from beeflow.cloud import provider

import openstack


class ChameleoncloudProvider(provider.Provider):
    """Chameleoncloud provider class."""

    def __init__(self, stack_name=None, **kwargs):
        """Chameleoncloud provider constructor."""
        self._stack_name = stack_name
        self._api = openstack.connect()
        # TODO: Chameleon set up

    # def create_node(self):
    def create_from_tempalte(self, template_file):
        """Create from a template file."""
        raise RuntimeError('create_node() is not implemented for Chameleoncloud')

    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""
        if self._stack_name is not None:
            stack = self._api.get_stack(self._stack_name)
            if stack is None:
                raise RuntimeError('Invalid stack %s' % (self._stack_name))
            outputs = {output['output_key']: output['output_value'] for output in stack['outputs']}
            if 'head_node_login_ip' in outputs:
                return outputs['head_node_login_ip']
            # TODO: Get the IP address from the stack output
        return None
