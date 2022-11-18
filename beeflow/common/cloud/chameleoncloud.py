"""Chameleon provider code."""
import openstack

from beeflow.common.cloud import provider


class ChameleoncloudProvider(provider.Provider):
    """Chameleoncloud provider class."""

    def __init__(self, stack_name=None, **_kwargs):
        """Chameleoncloud provider constructor."""
        self._stack_name = stack_name
        self._api = openstack.connect()

    def create_from_template(self, template_file):
        """Create from a template file."""
        raise RuntimeError(
            'create_from_template() is not implemented for Chameleoncloud. '
            'Use the Horizon interface instead'
        )

    def get_ext_ip_addr(self, node_name):  # noqa
        """Get the external IP address of the node, if it has one."""
        if self._stack_name is not None:
            stack = self._api.get_stack(self._stack_name)
            if stack is None:
                raise RuntimeError(f'Invalid stack {self._stack_name}')
            outputs = {output['output_key']: output['output_value'] for output in stack['outputs']}
            if 'head_node_login_ip' in outputs:
                return outputs['head_node_login_ip']
        return None
