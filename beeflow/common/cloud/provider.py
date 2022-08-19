"""Provider class, representing a specific Cloud provider."""
import abc


class Provider(abc.ABC):
    """Provider Abstract Base Class."""

    @abc.abstractmethod
    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""

    @abc.abstractmethod
    def setup_cloud(self, config):
        """Set up the cloud based on the config data."""


class MockProvider(Provider):
    """Mock provider class for testing."""

    def __init__(self, **kwargs):
        """Construct a mock provider."""

    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""
        return '100.100.100.100'

    def setup_cloud(self, config):
        """Set up the cloud based on the config data."""
