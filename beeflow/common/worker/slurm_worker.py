"""Slurm worker for work load management.

Builds command for submitting batch job.
"""

import subprocess
import json
import urllib
import getpass
import requests_unixsocket
import requests

from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)

log = bee_logging.setup(__name__)


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager."""

    def __init__(self, bee_workdir, openapi_version, **kwargs):
        """Create a new Slurm Worker object."""
        super().__init__(bee_workdir, **kwargs)
        # Pull slurm socket configs from kwargs (Uses getpass.getuser() instead
        # of os.getlogin() because of an issue with using getlogin() without a
        # controlling terminal)
        self.slurm_socket = kwargs.get('slurm_socket', f'/tmp/slurm_{getpass.getuser()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        # Note: Socket path is encoded, http request is not generally.
        self.slurm_url = f"http+unix://{encoded_path}/slurm/{openapi_version}"

    def build_text(self, task):
        """Build text for task script; use template if it exists."""
        task_save_path = self.task_save_path(task)
        crt_res = self.crt.run_text(task)
        requirements = dict(task.requirements)
        stdout_param = ['--output', task.stdout]
        stderr_param = ['--error', task.stderr]
        if task.stdout and task.stderr:
            main_command_srun_args = stdout_param + stderr_param
        elif task.stdout:
            main_command_srun_args = stdout_param
        elif task.stderr:
            main_command_srun_args = stderr_param
        else:
            main_command_srun_args = []
        nodes = task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=1)

        job_text = self.template.render(
            task_save_path=task_save_path,
            task_name=task.name,
            task_id=task.id,
            workflow_id=task.workflow_id,
            env_code=crt_res.env_code,
            pre_commands=crt_res.pre_commands,
            main_command=crt_res.main_command,
            post_commands=crt_res.post_commands,
            requirements=requirements,
            nodes=nodes,
            ntasks=ntasks,
            main_command_srun_args=main_command_srun_args,
            # Default MPI version
            mpi_version='pmi2',
        )
        return job_text

    def write_script(self, task):
        """Build task script; returns filename of script."""
        task_text = self.build_text(task)

        task_script = f'{self.task_save_path(task)}/{task.name}-{task.id}.sh'
        with open(task_script, 'w', encoding='UTF-8') as script_f:
            script_f.write(task_text)
            script_f.close()
        return task_script

    @staticmethod
    def query_job(job_id, session, slurm_url):
        """Query slurm for job status."""
        try:
            resp = session.get(f'{slurm_url}/job/{job_id}')

            if resp.status_code != 200:
                raise WorkerError(f'Failed to query job {job_id}')
            data = json.loads(resp.text)
            # Check for errors in the response
            check_slurm_error(data, f'Failed to query job {job_id}')
            # For some versions of slurm, the job_state isn't included on failure
            try:
                job_state = data['jobs'][0]['job_state']
            except (KeyError, IndexError) as exc:
                raise WorkerError(f'Failed to query job {job_id}') from exc
        except requests.exceptions.ConnectionError:
            job_state = "NOT_RESPONDING"
        return job_state

    def submit_job(self, script, session, slurm_url):
        """Worker submits job-returns (job_id, job_state)."""
        res = subprocess.run(['sbatch', '--parsable', script], text=True,  # noqa if we use check=True here, then we can't see stderr
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise WorkerError(f'Failed to submit job: {res.stderr}')
        job_id = int(res.stdout)
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
        try:
            resp = self.session.delete(f'{self.slurm_url}/job/{job_id}')
        except requests.exceptions.ConnectionError:
            return 'NOT_RESPONDING'
        # For some reason, some versions of slurmrestd are not returning an
        # HTTP error code, but just an error in the body
        errmsg = f'Unable to cancel job id {job_id}!'
        if resp.status_code != 200:
            raise WorkerError(f'{errmsg}: Bad response code: {resp.status_code}')
        try:
            data = resp.json()
            check_slurm_error(data, errmsg)
        except requests.exceptions.JSONDecodeError as exc:  # noqa requests is not installed in CI
            raise WorkerError(errmsg) from exc
        job_state = "CANCELLED"
        return job_state


def check_slurm_error(data, msg):
    """Check for an error in a Slurm response."""
    if 'errors' in data and data['errors']:
        err = data['errors'][0]
        desc = err['description']
        errmsg = err['error']
        raise WorkerError(f'{msg}: {errmsg} ({desc})')
