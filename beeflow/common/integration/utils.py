"""Utility code for running the integration tests."""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import subprocess
import time
import traceback
import uuid

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
        self.workdir = Path(workdir)
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

    @property
    def task_states(self):
        """Get the task states of the workflow."""
        return bee_client.query(self.wf_id)[1]

    def get_task_state_by_name(self, name):
        """Get the state of a task by name."""
        task_states = self.task_states
        return [task_state for _, task_name, task_state in task_states if task_name == name][0]

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

        fails = sum(1 if result is not None else 0 for _, result in results.items())
        self.display_results(results, fails)
        return 1 if fails > 0 else 0

    def display_results(self, results, fails):
        """Show the workflow results."""
        print('######## WORKFLOW RESULTS ########')
        passes = len(results) - fails
        print(f'{passes} passes, {fails} fails')
        for name, result in results.items():
            error = result
            if error is not None:
                print(f'{name}: {error}')
        print('##################################')


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
    ci_assert(workflow.status == 'Archived', f'bad workflow status {workflow.status}')


def check_workflow_failed(workflow):
    """Ensure that the workflow completed in a Failed state."""
    ci_assert(workflow.status == 'Archived/Failed',
              f'workflow did not fail as expected (final status: {workflow.status})')


def make_workflow_workdir(outer_workdir):
    """Create a workdir for the workflow run output files."""
    workdir = os.path.join(outer_workdir, uuid.uuid4().hex)
    os.makedirs(workdir)
    return workdir
