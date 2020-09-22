"""Slurm worker for work load management.

Builds command for submitting batch job.
"""

import os
import string
import subprocess
import json
import urllib
import requests_unixsocket

from beeflow.common.worker.worker import Worker
from beeflow.common.crt.crt_interface import ContainerRuntimeInterface

# Import all implemented container runtime drivers now
# No error if they don't exist
try:
    from beeflow.common.crt.crt_drivers import CharliecloudDriver
except ModuleNotFoundError:
    pass
try:
    from beeflow.common.crt.crt_drivers import SingularityDriver
except ModuleNotFoundError:
    pass


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager."""

    def __init__(self, **kwargs):
        """Create a new Slurm Worker object."""
        # Pull slurm socket configs from kwargs
        self.slurm_socket = kwargs.get('slurm_socket', f'/tmp/slurm_{os.getlogin()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        # Note: Socket path is encoded, http request is not generally.
        self.slurm_url = f"http+unix://{encoded_path}/slurm/v0.0.35"

        # Load appropriate container runtime driver, based on configs in kwargs
        try:
            self.tm_crt = kwargs['container_runtime']
        except KeyError:
            print("No container runtime specified in config, proceeding with caution.")
            self.tm_crt = None
            crt_driver = None
        finally:
            if self.tm_crt == 'Charliecloud':
                crt_driver = CharliecloudDriver
            elif self.tm_crt == 'Singularity':
                crt_driver = SingularityDriver
            self.crt = ContainerRuntimeInterface(crt_driver)

        # Get BEE workdir from config file
        self.workdir = kwargs['bee_workdir']

        # Get template for job, if option in configuration
        self.job_template = kwargs['job_template']
        if self.job_template:
            try:
                template_file = open(self.job_template, 'r')
                self.template_text = template_file.read()
                template_file.close()
            except ValueError as error:
                print(error)
        else:
            self.template_text = '#! /bin/bash\n#SBATCH\n'

    def build_text(self, task):
        """Build text for task script use template if it exists."""
        template_text = self.template_text
        template = string.Template(template_text)
        job_text = template.substitute({'name': task.name, 'id': task.id})
        crt_text = self.crt.script_text(task)
        job_text += crt_text
        return job_text

    def write_script(self, task):
        """Build task script; returns filename of script."""
        if not self.crt.image_exists(task):
            raise Exception('dockerImageId not accessible.')
        os.makedirs(f'{self.workdir}/worker', exist_ok=True)
        task_text = self.build_text(task)
        task_script = f'{self.workdir}/worker/{task.name}.sh'
        script_f = open(task_script, 'w')
        script_f.write(task_text)
        script_f.close()
        return task_script

    @staticmethod
    def query_job(job_id, session, slurm_url):
        """Query slurm for job status."""
        resp = session.get(f'{slurm_url}/job/{job_id}')
        if resp.status_code != 200:
            raise Exception (f'Unable to query job id {job_id}.')
        else:
            status = json.loads(resp.text)
            job_state = status['job_state']
        return job_state

    def submit_job(self, script, session, slurm_url):
        """Worker submits job-returns (job_id, job_state)."""
        job_st = subprocess.check_output(['sbatch', '--parsable', script],
                                         stderr=subprocess.STDOUT)
        job_id = int(job_st)
        job_state = self.query_job(job_id, session, slurm_url)
        return job_id, job_state

    def submit_task(self, task):
        """Worker builds & submits script."""
        task_script = self.write_script(task)
        job_id, job_state = self.submit_job(task_script, self.session, self.slurm_url)
        return job_id, job_state

    def query_task(self, job_id):
        """Worker queries job; returns job_state."""
        job_state = self.query_job(job_id, self.session, self.slurm_url)
        return job_state

    def cancel_task(self, job_id):
        """Worker cancels job returns job_state."""
        resp = self.session.delete(f'{self.slurm_url}/job/{job_id}')
        if resp.status_code != 200:
            raise Exception(f'Unable to cancel job id {job_id}!')
        else:
            job_state = "CANCELLED"
        return job_state

# Ignore module imported but unused error. No way to know which crt will be needed
# pylama:ignore=W0611
