#!/usr/bin/env python
"""CI workflow run script."""
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.client import bee_client
import subprocess
import os
import time


# Max time of each workflow
TIMEOUT = 300


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
                                       os.path.dirname(self.dockerfile)])
                subprocess.check_call(['ch-convert', '-i', 'ch-image', '-o', 'tar', self.name,
                                       self.tarball])
            except subprocess.CalledProcessError as error:
                raise CIError(
                    f'container build: {error}'
                ) from None
            self.done = True


class Workflow:
    """Workflow CI class for interacting with BEE."""

    def __init__(self, name, path, main_cwl, job_file, check_fn, containers):
        """Workflow constructor."""
        self.name = name
        self.path = path
        self.main_cwl = main_cwl
        self.job_file = job_file
        self.check_fn = check_fn
        self.containers = containers

    def run(self):
        """Attempt to submit, start and run the workflow to completion."""
        # Build all the containers first
        print('Building all containers')
        for ctr in self.containers:
            ctr.build()
        out_tarball = f'{self.name}.tgz'
        print('Creating the workflow tarball', out_tarball)
        try:
            subprocess.check_call(['tar', '-C', os.path.dirname(self.path), '-czf', out_tarball,
                                   os.path.basename(self.path)])
        except subprocess.CalledProcessError as error:
            raise CIError(
                f'workflow tar cmd: {error}'
            ) from None
        try:
            wf_id = bee_client.submit(self.name, out_tarball, self.main_cwl, self.job_file)
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
        self.check_fn()


def test_workflows(workflows):
    """Test run all workflows."""
    results = {}
    for wfl in workflows:
        try:
            wfl.run()
        except CIError as error:
            results[wfl.name] = error
        else:
            results[wfl.name] = None

    print('######## WORKFLOW RESULTS ########')
    fails = sum(1 if results[name] is not None else 0 for name in results)
    passes = len(results) - fails
    print(f'{passes} passes, {fails} fails')
    for name in results:
        error = results[name]
        if error is not None:
            print(f'{name}: {error}')
    print('##################################')


# Initialize BEE's config system
bc.init()

# Workflow check functions
def check_clamr():
    """Ensure that CLAMR was successful."""
    path = os.path.expanduser('~/CLAMR_movie.mp4')
    if not os.path.exists(path):
        raise CIError(f'CLAMR: missing output file "{path}"')


# Set up containers and workflows
clamr_ctr = Container('clamr', 'src/beeflow/data/dockerfiles/Dockerfile.clamr-ffmpeg',
                      '/tmp/clamr.tar.gz')
workflows = [
    Workflow('clamr', './src/beeflow/data/cwl/bee_workflows/clamr-ci', main_cwl='clamr_wf.cwl',
             job_file='clamr_job.yml', check_fn=check_clamr, containers=[clamr_ctr]),
]

# Run the workflows and then show completion results
test_workflows(workflows)
