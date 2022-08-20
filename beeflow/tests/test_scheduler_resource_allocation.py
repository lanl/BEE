"""Test the resource_allocation submodule of BEE."""
import json

from beeflow.scheduler import resource_allocation


def test_resource_simple():
    """Test creating a resource."""
    resource = resource_allocation.Resource(id_='test-resource', nodes=1)

    assert resource.id_ == 'test-resource'
    assert resource.nodes == 1
    assert resource.mem_per_node == 8192
    assert resource.gpus_per_node == 0


def test_resource_encode_decode_json():
    """Ensure that a resource can be encoded/decoded to/from JSON."""
    resource = resource_allocation.Resource(id_='test-resource', nodes=1)

    s = json.dumps(resource.encode())

    decoded = resource_allocation.Resource.decode(json.loads(s))
    assert decoded.id_ == 'test-resource'
    assert decoded.nodes == resource.nodes
    assert decoded.mem_per_node == resource.mem_per_node
    assert decoded.gpus_per_node == resource.gpus_per_node


def test_allocation_simple():
    """Test creating an allocation."""
    allocation = resource_allocation.Allocation(id_='resource-0', start_time=0,
                                                max_runtime=4, nodes=2)

    assert allocation.id_ == 'resource-0'
    assert allocation.start_time == 0
    assert allocation.max_runtime == 4
    assert allocation.nodes == 2


def test_allocation_encode_decode_json():
    """Test that an allocation can be encoded/decoded to/from JSON."""
    allocation = resource_allocation.Allocation(id_='resource-0', start_time=3,
                                                max_runtime=5, nodes=6)

    s = json.dumps(allocation.encode())

    decoded = resource_allocation.Allocation.decode(json.loads(s))
    assert decoded.id_ == allocation.id_
    assert decoded.start_time == allocation.start_time
    assert decoded.max_runtime == allocation.max_runtime
    assert decoded.nodes == allocation.nodes


def test_requirements_simple():
    """Test creating a requirement."""
    requirements = resource_allocation.Requirements(max_runtime=3, nodes=1)

    assert requirements.max_runtime == 3
    assert requirements.nodes == 1
    # TODO: Determine what the default per node requirements should be


def test_requirements_encode_decode_json():
    """Test that an allocation can be encoded/decoded to/from JSON."""
    requirements = resource_allocation.Requirements(max_runtime=1, nodes=3)

    s = json.dumps(requirements.encode())

    decoded = resource_allocation.Requirements.decode(json.loads(s))
    assert decoded.max_runtime == requirements.max_runtime
    assert decoded.nodes == requirements.nodes
# Ignore W0511: This is related to issue #333
# pylama:ignore=W0511
