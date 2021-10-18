"""Provider class, representing a specific Cloud provider."""
import abc


class Provider(abc.ABC):
    """Provider Abstract Base Class."""

    @abc.abstractmethod
    def __init__(self, **kwargs):
        """Cloud Provider default constructor."""

    @abc.abstractmethod
    def create_from_template(self, template_file):
        """Create the cloud from a template."""

    @abc.abstractmethod
    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""


class MockProvider(Provider):
    """Mock provider class for testing."""

    def __init__(self, **kwargs):
        """Mock provider constructor."""

    def create_from_template(self, template_file):
        """Create a node."""

    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""
        return '100.100.100.100'
