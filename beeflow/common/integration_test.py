from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import subprocess
import sys
import time
import traceback
import uuid
import yaml
import typer

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.client import bee_client


# Max time of each workflow
TIMEOUT = 90
INTEGRATION_TEST_DIR = os.path.expanduser('~/.beeflow-integration')


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
                                       '--force', 'seccomp', os.path.dirname(self.dockerfile)])
                subprocess.check_call(['ch-convert', '-i', 'ch-image', '-o', 'tar', self.name,
                                       self.tarball])
            except subprocess.CalledProcessError as error:
                raise CIError(
                    f'container build: {error}'
                ) from None
            self.done = True


class Workflow:
    """Workflow CI class for interacting with BEE."""

    def __init__(self, name, path, main_cwl, job_file, workdir, containers):
        """Workflow constructor."""
        self.name = name
        self.path = path
        self.main_cwl = main_cwl
        self.job_file = job_file
        self.workdir = workdir
        self.containers = containers
        self.wf_id = None
        self.tarball = None

    def run(self):
        """Attempt to submit and start the workflow."""
        # Build all the containers first
        print('Building all containers')
        for ctr in self.containers:
            ctr.build()
        try:
            tarball_dir = Path(self.path).parent
            tarball = f'{Path(self.path).name}.tgz'
            self.tarball = tarball_dir / tarball
            print('Creating the workflow tarball', self.tarball)
            bee_client.package(Path(self.path), Path(tarball_dir))
            print('Submitting and starting workflow')
            self.wf_id = bee_client.submit(self.name, self.tarball, self.main_cwl,
                                           self.job_file, self.workdir, no_start=False)
        except bee_client.ClientError as error:
            raise CIError(*error.args) from error

    @property
    def running(self):
        """Check if the workflow is running or about to run."""
        return bee_client.query(self.wf_id)[0] in ('Initializing', 'Waiting', 'Running', 'Pending')

    @property
    def status(self):
        """Get the status of the workflow."""
        return bee_client.query(self.wf_id)[0]

    def cleanup(self):
        """Clean up any leftover workflow data."""
        # Remove the generated tarball
        os.remove(self.tarball)


class TestRunner:
    """Test runner class."""

    def __init__(self):
        """Build a new test runner class."""
        self.test_cases = []
        self.timeout = TIMEOUT

    def add(self, ignore=False):
        """Decorate a test case and add it to the runner instance."""

        def wrap(test_case):
            """Wrap the function."""
            # First turn it into a contextmanager
            test_case = contextmanager(test_case)
            self.test_cases.append((test_case, ignore))
            return test_case

        return wrap

    def test_details(self):
        """Return a list of all the test details (test_name, ignore)."""
        return [(test_case.__name__, ignore) for test_case, ignore in self.test_cases]

    def _run_workflows(self, workflows):
        """Run a list of workflows to completion."""
        # Start all workflows at once
        for wfl in workflows:
            wfl.run()
        # Now run until all workflows are complete or until self.timeout is hit
        t = 0
        while t < self.timeout:
            if all(not wfl.running for wfl in workflows):
                # All workflows have completed
                break
            time.sleep(2)
            t += 2
        if t >= self.timeout:
            raise CIError('workflow timeout')

    def run(self, test_names=None):
        """Test run all test cases."""
        results = {}
        for test_case, ignore in self.test_cases:
            if test_names is not None:
                # Skip tests that aren't required to be run
                if test_case.__name__ not in test_names:
                    continue
            elif ignore:
                # Skip ignored tests
                continue
            outer_workdir = os.path.join(INTEGRATION_TEST_DIR, uuid.uuid4().hex)
            os.makedirs(outer_workdir)
            msg0 = f'Starting test {test_case.__name__}'
            msg1 = f'(running in "{outer_workdir}")'
            count = max(len(msg0), len(msg1))
            print('#' * count)
            print(msg0)
            print(msg1)
            print('-' * count)
            try:
                with test_case(outer_workdir) as workflows:
                    self._run_workflows(workflows)
            except CIError as error:
                traceback.print_exc()
                results[test_case.__name__] = error
                print('------')
                print('FAILED')
                print('------')
            else:
                results[test_case.__name__] = None
                print('------')
                print('PASSED')
                print('------')
                # Only remove the outer_workdir if it passed
                try:
                    shutil.rmtree(outer_workdir)
                except OSError as err:
                    print(f'WARNING: Failed to remove {outer_workdir}')
                    print(err)

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


TEST_RUNNER = TestRunner()


#
# Helper methods for running the test cases
#


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


def ci_assert(predicate, msg):
    """Assert that the predicate is True, or raise a CIError."""
    if not predicate:
        raise CIError(msg)


def check_path_exists(path):
    """Check that the specified path exists."""
    ci_assert(os.path.exists(path), f'expected file "{path}" does not exist')


def check_completed(workflow):
    """Ensure the workflow has a completed status."""
    ci_assert(workflow.status == 'Archived', f'Bad workflow status {workflow.status}')


#
# Inline workflow generation code
#

def yaml_dump(path, data):
    """Dump this data as a yaml file at path."""
    with open(path, 'w', encoding='utf-8') as fp:
        yaml.dump(data, fp, Dumper=yaml.CDumper)


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


def generate_simple_workflow(output_path, fname):
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

# Remove an existing base container
if BASE_CONTAINER in ch_image_list():
    ch_image_delete(BASE_CONTAINER)


@TEST_RUNNER.add()
def copy_container(outer_workdir):
    """Prepare, check results of using `beeflow:copyContainer` then do cleanup."""
    # `beeflow:copyContainer` workflow
    container_path = f'/tmp/copy_container-{uuid.uuid4().hex}.tar.gz'
    container_name = 'copy-container'
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    container = Container(container_name, DOCKER_FILE_PATH, container_path)
    workflow_path = os.path.join(outer_workdir, f'bee-cc-workflow-{uuid.uuid4().hex}')
    main_input = 'copy_container'
    docker_requirement = {
        'beeflow:copyContainer': container_path,
    }
    main_cwl, job_file = generate_builder_workflow(workflow_path, docker_requirement,
                                                   main_input)
    workflow = Workflow('copy-container', workflow_path,
                        main_cwl=main_cwl, job_file=job_file, workdir=workdir,
                        containers=[container])
    yield [workflow]
    check_completed(workflow)
    # Ensure the output file was created
    path = os.path.join(workdir, main_input)
    check_path_exists(path)
    os.remove(path)
    # Ensure that the container has been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(container_path)
    path = os.path.join(container_archive, basename)
    check_path_exists(path)
    os.remove(path)
    ch_image_delete(container_name)


@TEST_RUNNER.add()
def use_container(outer_workdir):
    """Prepare, check results of using `beeflow:useContainer` and clean up."""
    # `beeflow:useContainer` workflow
    container_path = os.path.join(outer_workdir, f'use_container-{uuid.uuid4().hex}.tar.gz')
    container_name = 'use-container'
    container_workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(container_workdir)
    container = Container(container_name, DOCKER_FILE_PATH, container_path)
    workflow_path = os.path.join(outer_workdir, f'bee-use-ctr-workflow-{uuid.uuid4().hex}')
    main_input = 'use_ctr'
    docker_requirement = {
        'beeflow:useContainer': container_path,
    }
    main_cwl, job_file = generate_builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = Workflow('use-container', workflow_path,
                        main_cwl=main_cwl, job_file=job_file,
                        workdir=container_workdir, containers=[container])
    yield [workflow]
    check_completed(workflow)
    path = os.path.join(container_workdir, main_input)
    check_path_exists(path)
    # This container should not have been copied into the container archive
    container_archive = bc.get('builder', 'container_archive')
    basename = os.path.basename(container_path)
    path = Path(container_archive, basename)
    ci_assert(
        not path.exists(),
        f'the container "{basename}" was copied into the container archive'
    )
    ch_image_delete(container_name)


@TEST_RUNNER.add()
def docker_file(outer_workdir):
    """Ensure that the `dockerFile` example ran properly and then clean up."""
    # `dockerFile` workflow
    workflow_path = os.path.join(outer_workdir, f'bee-df-workflow-{uuid.uuid4().hex}')
    # Copy the Dockerfile to the workdir path
    os.makedirs(workflow_path)
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    shutil.copy(DOCKER_FILE_PATH, os.path.join(workflow_path, 'Dockerfile'))
    container_name = 'docker_file_test'
    docker_requirement = {
        'dockerFile': 'Dockerfile',
        'beeflow:containerName': container_name,
    }
    main_input = 'docker_file'
    main_cwl, job_file = generate_builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = Workflow('docker-file', workflow_path,
                        main_cwl=main_cwl, job_file=job_file, workdir=workdir,
                        containers=[])
    yield [workflow]
    check_completed(workflow)
    path = os.path.join(workdir, main_input)
    check_path_exists(path)
    # The container should have been copied into the archive
    container_archive = bc.get('builder', 'container_archive')
    tarball = f'{container_name}.tar.gz'
    path = os.path.join(container_archive, tarball)
    check_path_exists(path)
    os.remove(path)
    # Check that the container is listed
    images = ch_image_list()
    ci_assert(container_name in images, f'cannot find expected container "{container_name}"')
    ch_image_delete(container_name)


@TEST_RUNNER.add()
def docker_pull(outer_workdir):
    """Prepare, then check that the `dockerPull` option was successful."""
    # `dockerPull` workflow
    workflow_path = os.path.join(outer_workdir, f'bee-dp-workflow-{uuid.uuid4().hex}')
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    container_name = BASE_CONTAINER
    docker_requirement = {
        'dockerPull': container_name,
    }
    main_input = 'docker_pull'
    main_cwl, job_file = generate_builder_workflow(
        workflow_path,
        docker_requirement,
        main_input,
    )
    workflow = Workflow('docker-pull', workflow_path,
                        main_cwl=main_cwl, job_file=job_file, workdir=workdir,
                        containers=[])
    yield [workflow]
    check_completed(workflow)
    path = os.path.join(workdir, main_input)
    check_path_exists(path)
    # Check that the image tarball is in the archive
    container_archive = bc.get('builder', 'container_archive')
    path = os.path.join(container_archive, f'{container_name}.tar.gz')
    check_path_exists(path)
    os.remove(path)
    # Commenting the below out for now; looks like Charliecloud 0.32 isn't
    # showing base containers for some reason?
    # Check for the image with `ch-image list`
    # images = ch_image_list()
    # ci_assert(container_name in images, f'could not find expected container "{container_name}"')
    # ch_image_delete(container_name)


@TEST_RUNNER.add()
def multiple_workflows(outer_workdir):
    """Test running three different workflows at the same time."""
    output_file = 'output_file'
    workflow_data = []
    workflows = []
    for i in range(3):
        workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
        os.makedirs(workdir)
        workflow_path = Path(outer_workdir, uuid.uuid4().hex)
        main_cwl, job_file = generate_simple_workflow(workflow_path, output_file)
        workflow = Workflow(f'multi-workflow-{i}', workflow_path,
                            main_cwl=main_cwl, job_file=job_file,
                            workdir=workdir, containers=[])
        workflow_data.append({
            'workdir': workdir,
            'workflow_path': workflow_path,
        })
        workflows.append(workflow)
    yield workflows
    for workflow in workflows:
        check_completed(workflow)
    for wfl_info in workflow_data:
        workdir = wfl_info['workdir']
        workflow_path = wfl_info['workflow_path']
        # Each test should have touched this file
        path = Path(workdir, output_file)
        check_path_exists(path)


@TEST_RUNNER.add(ignore=True)
def checkpoint_restart(outer_workdir):
    """Test the clamr-ffmpeg checkpoint restart workflow."""
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    workflow = Workflow('checkpoint-restart',
                        'beeflow/data/cwl/bee_workflows/clamr-wf-checkpoint',
                        main_cwl='clamr_wf.cwl', job_file='clamr_job.yml',
                        workdir=workdir, containers=[])
    yield [workflow]
    check_completed(workflow)
    # Check for the movie file
    path = Path(workdir, 'CLAMR_movie.mp4')
    check_path_exists(path)


@TEST_RUNNER.add(ignore=True)
def checkpoint_restart_failure(outer_workdir):
    """Test a checkpoint restart workflow that continues past 'num_retries'."""
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    workflow = Workflow('checkpoint-too-long',
                        'beeflow/data/cwl/bee_workflows/checkpoint-too-long',
                        main_cwl='workflow.cwl', job_file='input.yml',
                        workdir=workdir, containers=[])
    yield [workflow]
    ci_assert(workflow.status == 'Failed',
              f'Workflow did not fail as expected (final status: {workflow.status})')


def test_input_callback(arg):
    """Parse a list of tests separated by commas."""
    return arg.split(',') if arg is not None else None


def main(tests = typer.Option(None, '--tests', '-t',  # noqa (conflict on '=' sign)
                              callback=test_input_callback,
                              help='tests run as comma-separated string'),
         show_tests: bool = typer.Option(False, '--show-tests', '-s',  # noqa (conflict on '=' sign)
                                         help='show a list of all tests'),
         timeout: int = typer.Option(TIMEOUT, '--timeout', help='workflow timeout in seconds')):
    """Launch the integration tests."""
    if show_tests:
        print('INTEGRATION TEST CASES:')
        for test_name, ignore in TEST_RUNNER.test_details():
            print('*', test_name, '(ignored)' if ignore else '')
        return
    TEST_RUNNER.timeout = timeout
    # Run the workflows and then show completion results
    ret = TEST_RUNNER.run(tests)
    # ret = test_workflows(WORKFLOWS)
    # General clean up
    os.remove(DOCKER_FILE_PATH)
    sys.exit(ret)
# Ignore W0231: This is a user-defined exception and I don't think we need to call
#               __init__ on the base class.
# pylama:ignore=W0231
