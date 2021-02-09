"""Provider class, representing a specific Cloud provider."""
import abc


class Provider(abc.ABC):
    """Cloud Provider Class."""

    @abc.abstractmethod
    def __init__(self):
        """Cloud Provider default constructor."""

    @abc.abstractmethod
    def create_node(self, ram_per_vcpu, vcpu_per_node, ext_ip):
        """Create a node."""

    @abc.abstractmethod
    def wait(self):
        """Wait for complete setup."""


class MockNode:
    """Mock node class."""

    def __init__(self, ram_per_vcpu, vcpu_per_node, ext_ip):
        """Mock node constructor."""
        # TODO
        self.ram_per_vcpu = ram_per_vcpu
        self.vcpu_per_node = vcpu_per_node
        self.ext_ip = ext_ip

    def get_ext_ip(self):
        """Get external IP address."""
        return '100.100.100.100' if self.ext_ip else None


class MockProvider(Provider):
    """Mock provider class."""

    def __init__(self):
        """Mock provider constructor."""
        # TODO

    def create_node(self, ram_per_vcpu, vcpu_per_node, ext_ip):
        """Create a node."""
        # TODO
        return MockNode(ram_per_vcpu, vcpu_per_node, ext_ip)

    def wait(self):
        """Wait for complete setup."""
        # TODO


providers = {
    'Mock': MockProvider,  # Provider to be used for testing
}


def get_provider(name, **kwargs):
    """Return a Provider object for the given provider."""
    if name in providers:
        return providers[name](**kwargs)

    raise RuntimeError('Invalid provider "%s"' % name)
    # TODO
