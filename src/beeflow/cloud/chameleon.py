"""Chameleon provider code."""

import beeflow.cloud.provider as provider


class ChameleonProvider(provider.Provider):
    """Chameleon provider class."""

    def __init__(self):
        """Chameleon provider constructor."""

    def create_node(self):
        """Create a node."""
        raise RuntimeError('Not implemented')

    def wait(self):
        """Wait for complete setup."""
        raise RuntimeError('Not implemented')
