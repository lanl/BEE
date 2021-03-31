"""Provider class, representing a specific Cloud provider."""
import abc


class Provider(abc.ABC):
    """Provider Abstract Base Class."""

    @abc.abstractmethod
    def __init__(self, **kwargs):
        """Cloud Provider default constructor."""

    @abc.abstractmethod
    def create_node(self, node_name, startup_script, ext_ip=False):
        """Create a node."""

    @abc.abstractmethod
    def wait(self):
        """Wait for complete setup."""

    @abc.abstractmethod
    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""


class MockProvider(Provider):
    """Mock provider class for testing."""

    def __init__(self, **kwargs):
        """Mock provider constructor."""
        self._nodes = {}

    def create_node(self, node_name, startup_script, ext_ip=False):
        """Create a node."""
        self._nodes[node_name] = {
            'ext_ip': ext_ip,
        }

    def wait(self):
        """Wait for complete setup."""
        # TODO

    def get_ext_ip_addr(self, node_name):
        """Get the external IP address of the node, if it has one."""
        if self._nodes[node_name]['ext_ip']:
            return '100.100.100.100'
        return None
