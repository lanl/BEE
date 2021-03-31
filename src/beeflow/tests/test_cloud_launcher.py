"""Test beeflow cloud interface."""

import beeflow.cloud as cloud


PROVIDER = 'Mock'


def test_cloud_bee_user():
    """Test for the cloud user."""
    assert cloud.BEE_USER == 'bee'


def test_cloud_one_node():
    """Test cloud set up with a single node."""
    provider = cloud.get_provider(PROVIDER)

    provider.create_node('head-node', startup_script='#!/bin/sh\necho Test\n', ext_ip=True)
    # Wait for complete set up
    provider.wait()

    # Mock external IP address
    assert provider.get_ext_ip_addr('head-node') == '100.100.100.100'


def test_cloud_three_nodes():
    """Test cloud set up with a three nodes."""
    provider = cloud.get_provider(PROVIDER)

    node0, node1, node2 = 'node-0', 'node-1', 'node-2'
    provider.create_node(node0, startup_script='#!/bin/sh', ext_ip=True)
    provider.create_node(node1, startup_script='#!/bin/sh')
    provider.create_node(node2, startup_script='#!/bin/sh')
    # Wait for complete set up
    provider.wait()

    assert provider.get_ext_ip_addr(node0) == '100.100.100.100'
    assert provider.get_ext_ip_addr(node1) is None
    assert provider.get_ext_ip_addr(node2) is None


# TODO: Test creating a network
