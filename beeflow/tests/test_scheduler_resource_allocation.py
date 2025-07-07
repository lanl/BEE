"""Test the resource_allocation submodule of BEE."""

# Disable W0511: This is related to issue #333
# pylint:disable=W0511

import json

from beeflow.scheduler import resource_allocation, models


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
    allocation = models.Allocation(id_='resource-0', start_time=0,
                                                max_runtime=4, nodes=2)

    assert allocation.id_ == 'resource-0'
    assert allocation.start_time == 0
    assert allocation.max_runtime == 4
    assert allocation.nodes == 2


def test_requirements_simple():
    """Test creating a requirement."""
    requirements = models.SchedulerRequirements(max_runtime=3, nodes=1)

    assert requirements.max_runtime == 3
    assert requirements.nodes == 1
    # TODO: Determine what the default per node requirements should be

