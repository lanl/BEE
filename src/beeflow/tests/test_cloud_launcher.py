"""Test beeflow cloud interface.

This basically just tests the interface using the MockProvider class.
"""

import tempfile

import beeflow.cloud as cloud


PROVIDER = 'mock'

# TODO: Modify tests for template files


def test_cloud_bee_user():
    """Test for the cloud user."""
    assert cloud.BEE_USER == 'bee'


def test_cloud_one_node():
    """Test cloud set up with a single node."""
    provider = cloud.get_provider(PROVIDER)

    with tempfile.NamedTemporaryFile() as tmp:
        provider.create_from_template(tmp.name)

    # Mock external IP address
    assert provider.get_ext_ip_addr('head-node') == '100.100.100.100'

# TODO: Creating a network
