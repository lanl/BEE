"""Unit test module for the BEE DAG related modules."""

from pathlib import Path
import unittest
from beeflow.common.gdb import graphml_key_updater, generate_graph


REPO_PATH = Path(*Path(__file__).parts[:-3])


def find(path):
    """Find a path relative to the root of the repo."""
    return str(Path(REPO_PATH, path))


def test_parse_graphml():
    """Test parsing a GraphML file."""
    graphml_file = find("beeflow/data/graphml/cat-graphml")
    tree, root = graphml_key_updater.parse_graphml(graphml_file)
    assert isinstance(tree, ET.ElementTree)
    assert root.tag == '{http://graphml.graphdrawing.org/xmlns}graphml'


def test_find_missing_keys_valid_file():
    """Test finding the missing keys for a GraphML that isn't missing any keys."""
    graphml_file = find("beeflow/data/graphml/cat.graphml")
    tree, root = graphml_key_updater.parse_graphml(graphml_file)
    name_space = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    missing_keys = graphml_key_updater.find_missing_keys(root, name_space)
    assert missing_keys == set()
    

def test_find_missing_keys_invalid_file():
    """Test finding the missing keys for a GraphML that is missing the value key."""
    graphml_file = find("beeflow/data/graphml/invalid-clamr.graphml")
    tree, root = graphml_key_updater.parse_graphml(graphml_file)
    name_space = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    missing_keys = graphml_key_updater.find_missing_keys(root, name_space)
    assert missing_keys == {'value'}


def test_insert_missing_keys():
    """Test inserting missing keys to the GraphML."""
    graphml_file = find("beeflow/data/graphml/invalid-clamr.graphml")
    tree, root = graphml_key_updater.parse_graphml(graphml_file)
    name_space = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    missing_keys = {'value'}
    graphml_key_updater.insert_missing_keys(root, missing_keys, name_space)
    missing_keys = graphml_key_updater.find_missing_keys(root, name_space)
    assert missing_keys == set()


if __name__ == '__main__':
    unittest.main()
