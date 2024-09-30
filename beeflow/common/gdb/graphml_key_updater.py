"""Module to make sure all required keys are present."""

import xml.etree.ElementTree as ET
import os

from beeflow.common import paths

bee_workdir = paths.workdir()
dags_dir = os.path.join(bee_workdir, 'dags')
graphmls_dir = dags_dir + "/graphmls"

expected_keys = {"id", "name", "state", "class", "type", "value", "source",
                 "workflow_id", "base_command", "stdout", "stderr", "default",
                 "prefix", "position", "value_from", "glob"}

default_key_definitions = {
    "id": {"for": "node", "attr.name": "id", "attr.type": "string"},
    "name": {"for": "node", "attr.name": "name", "attr.type": "string"},
    "state": {"for": "node", "attr.name": "state", "attr.type": "string"},
    "class": {"for": "node", "attr.name": "class", "attr.type": "string"},
    "type": {"for": "node", "attr.name": "type", "attr.type": "string"},
    "value": {"for": "node", "attr.name": "value", "attr.type": "string"},
    "source": {"for": "node", "attr.name": "source", "attr.type": "string"},
    "workflow_id": {"for": "node", "attr.name": "workflow_id", "attr.type": "string"},
    "base_command": {"for": "node", "attr.name": "base_command", "attr.type": "string"},
    "stdout": {"for": "node", "attr.name": "stdout", "attr.type": "string"},
    "stderr": {"for": "node", "attr.name": "stderr", "attr.type": "string"},
    "default": {"for": "node", "attr.name": "default", "attr.type": "string"},
    "prefix": {"for": "node", "attr.name": "prefix", "attr.type": "string"},
    "position": {"for": "node", "attr.name": "position", "attr.type": "long"},
    "value_from": {"for": "node", "attr.name": "value_from", "attr.type": "string"},
    "glob": {"for": "node", "attr.name": "glob", "attr.type": "string"},
}


def update_graphml(wf_id):
    """Update GraphML file by ensuring required keys are present and updating its structure."""
    short_id = wf_id[:6]
    graphml_path = graphmls_dir + "/" + short_id + ".graphml"
    # Parse the GraphML file and preserve namespaces
    tree = ET.parse(graphml_path)
    root = tree.getroot()

    name_space = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    defined_keys = {key.attrib['id'] for key in root.findall('graphml:key', name_space)}
    used_keys = {data.attrib['key'] for data in root.findall('.//graphml:data', name_space)}

    missing_keys = used_keys - defined_keys

    # Insert default key definitions for missing keys
    for missing_key in missing_keys:
        if missing_key in expected_keys:
            default_def = default_key_definitions[missing_key]
            key_element = ET.Element(f'{{{name_space["graphml"]}}}key',
                                     id=missing_key,
                                     **default_def)
            root.insert(0, key_element)

    # Save the updated GraphML file by overwriting the original one
    tree.write(graphml_path, encoding='UTF-8', xml_declaration=True)
