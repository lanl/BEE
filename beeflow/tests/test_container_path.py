"""Tests for container path conversion."""

from beeflow.common.container_path import convert_path


def test_empty():
    """Test an empty bind mounts list."""
    assert convert_path('/home/test', {}) == '/home/test'
    assert convert_path('/usr', {}) == '/usr'


def test_nonempty():
    """Test a non-empty bind mount list."""
    bind_mounts = {
        '/prefix/home/test': '/home/test',
        '/usr/projects/some-project': '/mnt/0',
        '/data': '/mnt/1',
    }

    assert convert_path('/prefix/home/test/some/path', bind_mounts) == '/home/test/some/path'
    assert convert_path('/usr/projects/some-project/123', bind_mounts) == '/mnt/0/123'
    assert convert_path('/data/1/2/3', bind_mounts) == '/mnt/1/1/2/3'
    assert convert_path('/some/other/path', bind_mounts) == '/some/other/path'
