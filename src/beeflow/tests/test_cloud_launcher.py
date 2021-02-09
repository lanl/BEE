"""Test beeflow cloud interface."""

import beeflow.cloud as cloud


PROVIDER = 'Mock'


def test_cloud_bee_user():
    """Test for the cloud user."""
    assert cloud.BEE_USER == 'bee'


def test_cloud_one_node():
    """Test cloud set up with a single node."""
    provider = cloud.get_provider(PROVIDER)
    c = cloud.Cloud(provider, priv_key_file=None)

    node = c.create_node(ram_per_vcpu=2, vcpu_per_node=2, ext_ip=True)
    # Wait for complete set up
    c.wait()

    # Mock external IP address
    assert node.get_ext_ip() == '100.100.100.100'
    assert node.ram_per_vcpu == 2
    assert node.vcpu_per_node == 2


def test_cloud_three_nodes():
    """Test cloud set up with a three nodes."""
    provider = cloud.get_provider(PROVIDER)
    c = cloud.Cloud(provider, priv_key_file=None)

    node0 = c.create_node(ram_per_vcpu=4, vcpu_per_node=8, ext_ip=True)
    node1 = c.create_node(ram_per_vcpu=2, vcpu_per_node=2, ext_ip=None)
    node2 = c.create_node(ram_per_vcpu=2, vcpu_per_node=2, ext_ip=None)
    # Wait for complete set up
    c.wait()

    assert node0.get_ext_ip() == '100.100.100.100'
    assert node0.ram_per_vcpu == 4
    assert node0.vcpu_per_node == 8
    assert node1.get_ext_ip() is None
    assert node1.ram_per_vcpu == 2
    assert node1.vcpu_per_node == 2
    assert node2.get_ext_ip() is None
    assert node2.ram_per_vcpu == 2
    assert node2.vcpu_per_node == 2
