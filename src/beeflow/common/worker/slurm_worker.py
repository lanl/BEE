"""Slurm worker for work load management.

Builds command for submitting batch job.
"""

import os
import string
import subprocess
import json
import urllib
import requests_unixsocket
import requests
import getpass

from beeflow.common.worker.worker import Worker
from beeflow.cli import log
import beeflow.common.log as bee_logging


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager."""

    def __init__(self, bee_workdir, **kwargs):
        """Create a new Slurm Worker object."""
        super().__init__(bee_workdir, **kwargs)
        # Pull slurm socket configs from kwargs (Uses getpass.getuser() instead
        # of os.getlogin() because of an issue with using getlogin() without a
        # controlling terminal)
        self.slurm_socket = kwargs.get('slurm_socket', f'/tmp/slurm_{getpass.getuser()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        # Note: Socket path is encoded, http request is not generally.
        self.slurm_url = f"http+unix://{encoded_path}/slurm/v0.0.35"
        # Setup logger
        bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='SlurmWorker.log')

    def write_script(self, task):
        """Build task script; returns filename of script."""
        script_dir = f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'
        os.makedirs(script_dir, exist_ok=True)
        task_text = self.build_text(task)
        task_script = f'{script_dir}/{task.name}-{task.id}.sh'
        script_f = open(task_script, 'w')
        script_f.write(task_text)
        script_f.close()
        return task_script

    @staticmethod
    def query_job(job_id, session, slurm_url):
        """Query slurm for job status."""
        try:
            resp = session.get(f'{slurm_url}/job/{job_id}')

            if resp.status_code != 200:
                job_state = f"BAD_RESPONSE_{resp.status_code}"
            else:
                status = json.loads(resp.text)
                job_state = status['job_state']
        except requests.exceptions.ConnectionError:
            job_state = "NOT_RESPONDING"
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
        """Worker cancels job, returns job_state."""
        resp = self.session.delete(f'{self.slurm_url}/job/{job_id}')
        if resp.status_code != 200:
            raise Exception(f'Unable to cancel job id {job_id}!')
        job_state = "CANCELLED"
        return job_state
# Ignore R1732: Warnign about using open without "with' context. Seems like personal preference.
# pylama:ignore=R1732
