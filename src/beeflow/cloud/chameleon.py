"""Chameleon provider code."""

import beeflow.cloud.provider as provider


class ChameleonProvider(provider.Provider):
    """Chameleon provider class."""

    def __init__(self, **kwargs):
        """Chameleon provider constructor."""
        # TODO: Chameleon set up

    # def create_node(self):
    def create_node(self, node_name, startup_script, ext_ip=False):
        """Create a node."""
        raise RuntimeError('create_node() is not implemented for Chameleoncloud')

    def wait(self):
        """Wait for complete setup."""
        raise RuntimeError('wait() is not implemented implemented for Chameleoncloud')

    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""
        # TODO: Get the external IP address from the Chameleon API
