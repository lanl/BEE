#!/usr/bin/env python
"""CI workflow run script."""
import subprocess
import os
import shutil
import sys
import time
import uuid
import yaml

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.client import bee_client


# Max time of each workflow
TIMEOUT = 120


class CIError(Exception):
    """CI error class."""

    def __init__(self, *args):
        """Initialize the error with default args."""
        self.args = args


class Container:
    """Container CI class for building BEE containers."""

    def __init__(self, name, dockerfile, tarball):
        """BEE CI container constructor."""
        self.name = name
        self.dockerfile = dockerfile
        self.tarball = tarball
        self.done = False

    def build(self):
        """Build the containers and save them in the proper location."""
        if not self.done:
            try:
                subprocess.check_call(['ch-image', 'build', '-f', self.dockerfile, '-t', self.name,
                                       '--force', os.path.dirname(self.dockerfile)])
                subprocess.check_call(['ch-convert', '-i', 'ch-image', '-o', 'tar', self.name,
                                       self.tarball])
            except subprocess.CalledProcessError as error:
                raise CIError(
                    f'container build: {error}'
                ) from None
            self.done = True


class Workflow:
    """Workflow CI class for interacting with BEE."""

    def __init__(self, name, path, tarball, main_cwl, job_file, workdir, containers, check_cleanup_fn=None):
        """Workflow constructor."""
        self.name = name
        self.path = path
        self.tarball = tarball
        self.main_cwl = main_cwl
        self.job_file = job_file
        self.workdir = workdir
        self.containers = containers
        self.check_cleanup_fn = check_cleanup_fn

    def check_cleanup(self, fn):
        """Check cleanup decorator function."""

        def decorator():
            """Decorate the input function fn."""
            fn()

        self.check_cleanup_fn = fn
        return decorator

    def run(self):
        """Attempt to submit, start and run the workflow to completion."""
        try:
            self._run()
        finally:
            self.check_cleanup_fn()

    def _run(self):
        """Attempt to submit, start and run the workflow to completion (internal version)."""
        # Build all the containers first
        print('Building all containers')
        for ctr in self.containers:
            ctr.build()
        print('Creating the workflow tarball', self.tarball)
        try:
            subprocess.check_call(['tar', '-C', os.path.dirname(self.path), '-czf', self.tarball,
                                   os.path.basename(self.path)])
        except subprocess.CalledProcessError as error:
            raise CIError(
                f'workflow tar cmd: {error}'
            ) from None
        try:
            wf_id = bee_client.submit(self.name, self.tarball, self.main_cwl, self.job_file, self.workdir)
            bee_client.start(wf_id)
            time.sleep(2)
            t = 0
            while bee_client.query(wf_id)[0] == 'Running' and t < TIMEOUT:
                time.sleep(4)
                t += 4
        except bee_client.ClientError as error:
            raise CIError(*error.args) from None
        if t >= TIMEOUT:
            raise CIError('timeout exceeded')


def test_workflows(wfls):
    """Test run all workflows."""
    results = {}
    for wfl in wfls:
        try:
            wfl.run()
        except CIError as error:
            results[wfl.name] = error
        else:
            results[wfl.name] = None

    print('######## WORKFLOW RESULTS ########')
    fails = sum(1 if result is not None else 0 for name, result in results.items())
    passes = len(results) - fails
    print(f'{passes} passes, {fails} fails')
    for name, result in results.items():
        error = result
        if error is not None:
            print(f'{name}: {error}')
    print('##################################')
    return 1 if fails > 0 else 0


# Initialize BEE's config system
bc.init()


def ch_image_delete(img_name):
    """Execute a ch-image delete [img_name]."""
    try:
        subprocess.check_call(['ch-image', 'delete', img_name])
    except subprocess.CalledProcessError:
        raise CIError(
            f'failed when calling `ch-image delete {img_name}` to clean up'
        ) from None


def ch_image_list():
    """Execute a ch-image list and return the images."""
    try:
        res = subprocess.run(['ch-image', 'list'], stdout=subprocess.PIPE, check=True)
        output = res.stdout.decode(encoding='utf-8')
        images = [img for img in output.split('\n') if img]
        return images
    except subprocess.CalledProcessError as err:
        raise CIError(f'failed when calling `ch-image list`: {err}') from err


def check_path_exists(path):
    """Check that the specified path exists."""
    if not os.path.exists(path):
        raise CIError(f'expected file "{path}" does not exist')


#
# Inline workflow generation code
#


def generate_builder_workflow(output_path, docker_requirement, main_input):
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
    with open(os.path.join(output_path, main_cwl_file), 'w', encoding='utf-8') as fp:
        yaml.dump(main_cwl_data, fp, Dumper=yaml.CDumper)

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
    with open(os.path.join(output_path, step0_file), 'w', encoding='utf-8') as fp:
        yaml.dump(step0_data, fp, Dumper=yaml.CDumper)

    job_file = 'job.yml'
    job_data = {
        'main_input': main_input,
    }
    with open(os.path.join(output_path, job_file), 'w', encoding='utf-8') as fp:
        yaml.dump(job_data, fp, Dumper=yaml.CDumper)

    return (main_cwl_file, job_file)


BASE_CONTAINER = 'alpine'
SIMPLE_DOCKERFILE = """
# Dummy docker file that really doesn't do much
FROM alpine

# Install something that has minimal dependencies
RUN apk update && apk add bzip2
"""
# Dump the Dockerfile to a path that the later code can reference
DOCKER_FILE_PATH = os.path.join('/tmp', f'Dockerfile-{uuid.uuid4().hex}')
with open(DOCKER_FILE_PATH, 'w', encoding='utf-8') as docker_file_fp:
    docker_file_fp.write(SIMPLE_DOCKERFILE)

#
# Workflows setup
#


WORKFLOWS = []

# Remove an existing base container
if BASE_CONTAINER in ch_image_list():
    ch_image_delete(BASE_CONTAINER)


# `beeflow:copyContainer` workflow
CC_CONTAINER_PATH = f'/tmp/copy_container-{uuid.uuid4().hex}.tar.gz'
CC_CONTAINER_NAME = 'copy-container'
CC_WORKDIR = os.path.expanduser(f'~/{uuid.uuid4().hex}')
os.makedirs(CC_WORKDIR)
CC_CONTAINER = Container(CC_CONTAINER_NAME, DOCKER_FILE_PATH, CC_CONTAINER_PATH)
CC_WORKFLOW_PATH = os.path.join('/tmp', f'bee-cc-workflow-{uuid.uuid4().hex}')
CC_WORKFLOW_TARBALL = f'{CC_WORKFLOW_PATH}.tgz'
CC_MAIN_INPUT = 'copy_container'
CC_DOCKER_REQUIREMENT = {
    'beeflow:copyContainer': CC_CONTAINER_PATH,
}
CC_MAIN_CWL, CC_JOB_FILE = generate_builder_workflow(CC_WORKFLOW_PATH, CC_DOCKER_REQUIREMENT,
                                                     CC_MAIN_INPUT)
CC_WORKFLOW = Workflow('copy-container', CC_WORKFLOW_PATH, CC_WORKFLOW_TARBALL,
                       main_cwl=CC_MAIN_CWL, job_file=CC_JOB_FILE, workdir=CC_WORKDIR,
                       containers=[CC_CONTAINER])
WORKFLOWS.append(CC_WORKFLOW)


@CC_WORKFLOW.check_cleanup
def copy_container_check_cleanup():
    """Ensure that using `beeflow:copyContainer` was successful and then do cleanup."""
    # Ensure the output file was created
    path = os.path.join(CC_WORKDIR, CC_MAIN_INPUT)
    check_path_exists(path)
    os.remove(path)
    # Ensure that the container has been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(CC_CONTAINER_PATH)
    path = os.path.join(container_archive, basename)
    check_path_exists(path)
    os.remove(path)
    ch_image_delete(BASE_CONTAINER)
    ch_image_delete(CC_CONTAINER_NAME)
    # Delete the generated container
    shutil.rmtree(CC_WORKFLOW_PATH)
    os.remove(CC_CONTAINER_PATH)
    os.remove(CC_WORKFLOW_TARBALL)
    shutil.rmtree(CC_WORKDIR)


# `beeflow:useContainer` workflow
USE_CONTAINER_PATH = os.path.expanduser(f'~/use_container-{uuid.uuid4().hex}.tar.gz')
USE_CONTAINER_NAME = 'use-container'
USE_CONTAINER_WORKDIR = os.path.expanduser(f'~/{uuid.uuid4().hex}')
os.makedirs(USE_CONTAINER_WORKDIR)
USE_CONTAINER = Container(USE_CONTAINER_NAME, DOCKER_FILE_PATH, USE_CONTAINER_PATH)
USE_CONTAINER_WORKFLOW_PATH = os.path.join('/tmp', f'bee-use-ctr-workflow-{uuid.uuid4().hex}')
USE_CONTAINER_WORKFLOW_TARBALL = f'{USE_CONTAINER_WORKFLOW_PATH}.tgz'
USE_CONTAINER_MAIN_INPUT = 'use_ctr'
USE_CONTAINER_DOCKER_REQUIREMENT = {
    'beeflow:useContainer': USE_CONTAINER_PATH,
}
USE_CONTAINER_MAIN_CWL, USE_CONTAINER_JOB_FILE = generate_builder_workflow(
    USE_CONTAINER_WORKFLOW_PATH,
    USE_CONTAINER_DOCKER_REQUIREMENT,
    USE_CONTAINER_MAIN_INPUT,
)
USE_CONTAINER_WORKFLOW = Workflow('use-container', USE_CONTAINER_WORKFLOW_PATH,
                                  USE_CONTAINER_WORKFLOW_TARBALL, main_cwl=USE_CONTAINER_MAIN_CWL,
                                  job_file=USE_CONTAINER_JOB_FILE, workdir=USE_CONTAINER_WORKDIR,
                                  containers=[USE_CONTAINER])
WORKFLOWS.append(USE_CONTAINER_WORKFLOW)


@USE_CONTAINER_WORKFLOW.check_cleanup
def use_ctr_check_cleanup():
    """Check that the `beeflow:useContainer` example worked properly and then clean up."""
    path = os.path.join(USE_CONTAINER_WORKDIR, USE_CONTAINER_MAIN_INPUT)
    check_path_exists(path)
    os.remove(path)
    # This container should not have been copied into the container archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(USE_CONTAINER_PATH)
    path = os.path.join(container_archive, basename)
    if os.path.exists(path):
        raise CIError(
            f'the container "{basename}" was copied into the container archive, but shouldn\'t '
            'have been'
        )
    ch_image_delete(BASE_CONTAINER)
    ch_image_delete(USE_CONTAINER_NAME)
    # Delete both the workflow path and the container generated
    shutil.rmtree(USE_CONTAINER_WORKFLOW_PATH)
    os.remove(USE_CONTAINER_PATH)
    os.remove(USE_CONTAINER_WORKFLOW_TARBALL)
    shutil.rmtree(USE_CONTAINER_WORKDIR)


# `dockerFile` workflow
DF_WORKFLOW_PATH = os.path.join('/tmp', f'bee-df-workflow-{uuid.uuid4().hex}')
# Copy the Dockerfile to the workdir path
os.makedirs(DF_WORKFLOW_PATH)
shutil.copy(DOCKER_FILE_PATH, os.path.join(DF_WORKFLOW_PATH, 'Dockerfile'))
# Workflow tarball name
DF_WORKFLOW_TARBALL = f'{DF_WORKFLOW_PATH}.tgz'
DF_WORKDIR = os.path.expanduser(f'~/{uuid.uuid4().hex}')
os.makedirs(DF_WORKDIR)
DF_CONTAINER_NAME = 'docker_file_test'
DF_DOCKER_REQUIREMENT = {
    'dockerFile': 'Dockerfile',
    'beeflow:containerName': DF_CONTAINER_NAME,
}
DF_MAIN_INPUT = 'docker_file'
DF_MAIN_CWL, DF_JOB_FILE = generate_builder_workflow(DF_WORKFLOW_PATH, DF_DOCKER_REQUIREMENT,
                                                     DF_MAIN_INPUT)
DF_WORKFLOW = Workflow('docker-file', DF_WORKFLOW_PATH, DF_WORKFLOW_TARBALL, main_cwl=DF_MAIN_CWL,
                       job_file=DF_JOB_FILE, workdir=DF_WORKDIR, containers=[])
WORKFLOWS.append(DF_WORKFLOW)


@DF_WORKFLOW.check_cleanup
def docker_file_check_cleanup():
    """Ensure that the `dockerFile` example ran properly and then clean up."""
    path = os.path.join(DF_WORKDIR, DF_MAIN_INPUT)
    check_path_exists(path)
    os.remove(path)
    # The container should have been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    tarball = f'{DF_CONTAINER_NAME}.tar.gz'
    path = os.path.join(container_archive, tarball)
    check_path_exists(path)
    os.remove(path)
    # Check that the container is listed
    images = ch_image_list()
    if DF_CONTAINER_NAME not in images:
        raise CIError(f'cannot find expected container "{DF_CONTAINER_NAME}"')
    ch_image_delete(BASE_CONTAINER)
    ch_image_delete(DF_CONTAINER_NAME)
    # Delete the generated workflow
    shutil.rmtree(DF_WORKFLOW_PATH)
    os.remove(DF_WORKFLOW_TARBALL)
    shutil.rmtree(DF_WORKDIR)


# `dockerPull` workflow
DP_WORKFLOW_PATH = os.path.join('/tmp', f'bee-dp-workflow-{uuid.uuid4().hex}')
DP_WORKFLOW_TARBALL = f'{DP_WORKFLOW_PATH}.tgz'
DP_CONTAINER_NAME = BASE_CONTAINER
DP_DOCKER_REQUIREMENT = {
    'dockerPull': DP_CONTAINER_NAME,
}
DP_MAIN_INPUT = 'docker_pull'
DP_WORKDIR = os.path.expanduser(f'~/{uuid.uuid4().hex}')
os.makedirs(DP_WORKDIR)
DP_MAIN_CWL, DP_JOB_FILE = generate_builder_workflow(DP_WORKFLOW_PATH, DP_DOCKER_REQUIREMENT,
                                                     DP_MAIN_INPUT)
DP_WORKFLOW = Workflow('docker-pull', DP_WORKFLOW_PATH, DP_WORKFLOW_TARBALL, main_cwl=DP_MAIN_CWL,
                       job_file=DP_JOB_FILE, workdir=DP_WORKDIR, containers=[])
WORKFLOWS.append(DP_WORKFLOW)


@DP_WORKFLOW.check_cleanup
def docker_pull_check_cleanup():
    """Check that the `dockerPull` option was successful and then do cleanup."""
    path = os.path.join(DP_WORKDIR, DP_MAIN_INPUT)
    check_path_exists(path)
    os.remove(path)
    # Check that the image tarball is in the archive
    container_archive = bc.get('builder', 'container_archive')
    path = os.path.join(container_archive, f'{DP_CONTAINER_NAME}.tar.gz')
    check_path_exists(path)
    os.remove(path)
    # Check for the image with `ch-image list`
    images = ch_image_list()
    if DP_CONTAINER_NAME not in images:
        raise CIError(f'could not find expected container "{DP_CONTAINER_NAME}"')
    ch_image_delete(DP_CONTAINER_NAME)
    # Delete the workflow path
    shutil.rmtree(DP_WORKFLOW_PATH)
    os.remove(DP_WORKFLOW_TARBALL)
    shutil.rmtree(DP_WORKDIR)


# Run the workflows and then show completion results
ret = test_workflows(WORKFLOWS)
# General clean up
os.remove(DOCKER_FILE_PATH)
sys.exit(ret)
# Ignore W0231: This is a user-defined exception and I don't think we need to call
#               __init__ on the base class.
# pylama:ignore=W0231
