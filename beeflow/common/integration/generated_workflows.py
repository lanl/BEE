"""Inline workflow generation code."""
from pathlib import Path
import os
import uuid
import yaml

from beeflow.common.integration import utils


BASE_CONTAINER = 'alpine'
SIMPLE_DOCKERFILE = """
# Dummy docker file that really doesn't do much
FROM alpine

# Install something that has minimal dependencies
RUN apk update && apk add bzip2
"""
# Dump the Dockerfile to a path that the later code can reference
DOCKER_FILE_PATH = os.path.join('/tmp', f'Dockerfile-{uuid.uuid4().hex}')


def yaml_dump(path, data):
    """Dump this data as a yaml file at path."""
    with open(path, 'w', encoding='utf-8') as fp:
        yaml.dump(data, fp, Dumper=yaml.CDumper)


def builder_workflow(output_path, docker_requirement, main_input):
    """Generate a base workflow to be used for testing the builder."""
    os.makedirs(output_path, exist_ok=True)
    main_cwl_file = 'workflow.cwl'
    main_cwl_data = {
        'cwlVersion': 'v1.0',
        'class': 'Workflow',
        'inputs': {
            'main_input': 'string',
        },
        'outputs': {
            'main_output': {
                'outputSource': 'step0/step_output',
                'type': 'File',
            },
        },
        'steps': {
            'step0': {
                'run': 'step0.cwl',
                'in': {
                    'step_input': 'main_input',
                },
                'out': ['step_output'],
                'hints': {
                    'DockerRequirement': docker_requirement,
                },
            }
        },
    }
    yaml_dump(os.path.join(output_path, main_cwl_file), main_cwl_data)

    step0_file = 'step0.cwl'
    step0_data = {
        'cwlVersion': 'v1.0',
        'class': 'CommandLineTool',
        'baseCommand': 'touch',
        'inputs': {
            'step_input': {
                'type': 'string',
                'inputBinding': {
                    'position': 1,
                },
            },
        },
        'outputs': {
            'step_output': {
                'type': 'stdout',
            }
        },
        'stdout': 'output.txt',
    }
    yaml_dump(os.path.join(output_path, step0_file), step0_data)

    job_file = 'job.yml'
    job_data = {
        'main_input': main_input,
    }
    yaml_dump(os.path.join(output_path, job_file), job_data)

    return (main_cwl_file, job_file)


def simple_workflow(output_path, fname):
    """Generate a simple workflow."""
    os.makedirs(output_path, exist_ok=True)

    task0_cwl = 'task0.cwl'
    main_cwl = 'main.cwl'
    main_cwl_file = str(Path(output_path, main_cwl))
    main_cwl_data = {
        'cwlVersion': 'v1.0',
        'class': 'Workflow',
        'requirements': {},
        'inputs': {
            'in_fname': 'string',
        },
        'outputs': {
            'out': {
                'type': 'File',
                'outputSource': 'task0/out',
            },
        },
        'steps': {
            'task0': {
                'run': task0_cwl,
                'in': {
                    'fname': 'in_fname',
                },
                'out': ['out'],
            },
        },
    }
    yaml_dump(main_cwl_file, main_cwl_data)

    task0_cwl_file = str(Path(output_path, task0_cwl))
    task0_data = {
        'cwlVersion': 'v1.0',
        'class': 'CommandLineTool',
        'baseCommand': 'touch',
        'inputs': {
            'fname': {
                'type': 'string',
                'inputBinding': {
                    'position': 1,
                },
            },
        },
        'stdout': 'touch.log',
        'outputs': {
            'out': {
                'type': 'stdout',
            }
        }
    }
    yaml_dump(task0_cwl_file, task0_data)

    job_yaml = 'job.yaml'
    job_file = str(Path(output_path, job_yaml))
    job_data = {
        'in_fname': fname,
    }
    yaml_dump(job_file, job_data)
    return (main_cwl, job_yaml)


def init():
    """Initialize files and the container runtime."""
    with open(DOCKER_FILE_PATH, 'w', encoding='utf-8') as docker_file_fp:
        docker_file_fp.write(SIMPLE_DOCKERFILE)

    # Remove an existing base container
    if BASE_CONTAINER in utils.ch_image_list():
        utils.ch_image_delete(BASE_CONTAINER)
