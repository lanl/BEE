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
from beeflow.common.config.config_driver import BeeConfig

# Check configuration file for container runtime.
bc = BeeConfig()
tm_crt = bc.userconfig['task_manager'].get('container_runtime')
if tm_crt == 'Charliecloud':
    from beeflow.common.crt.crt_drivers import CharliecloudDriver as CrtDriver
elif tm_crt == 'Singularity':
    from beeflow.common.crt.crt_drivers import SingularityDriver as CrtDriver
else:
    print("Container Runtime not supported!")


def build_text(task, template_file):
    """Build text for task script use template if it exists."""
    job_template = ''
    try:
        template_f = open(template_file, 'r')
        job_template = template_f.read()
        template_f.close()
    except OSError:
        print('\nNo job_template: creating a simple job template!')
        job_template = '#! /bin/bash\n#SBATCH\n'
    template = string.Template(job_template)
    job_text = template.substitute({'name': task.name, 'id': task.id})
    crt_text = crt.script_text(task)
    job_text += crt_text
    return job_text


def write_script(task):
    """Build task script; returns (1, filename) or (-1, error_message)."""
    success = -1
    if not crt.image_exists(task):
        return success, "dockerImageId is not a valid image"
    # for now using fixed directory for task manager scripts and write them out
    # we may keep them in memory and only write for a debug or logging option
    # make directory (now uses date, should be workflow name or id?)
    workdir = bc.userconfig['DEFAULT'].get('bee_workdir')
    os.makedirs(f'{workdir}/worker', exist_ok=True)
    template_file = f'{workdir}/worker/job.template'
    task_text = build_text(task, template_file)
    task_script = f'{workdir}/worker/{task.name}.sh'
    try:
        script_f = open(task_script, 'w')
        script_f.write(task_text)
        script_f.close()
        success = 1
    except subprocess.CalledProcessError as error:
        task_script = error.output.decode('utf-8')
    return success, task_script


def query_job(job_id, session, slurm_url):
    """Query slurm for job status."""
    resp = session.get(f'{slurm_url}/job/{job_id}')
    if resp.status_code != 200:
        query_success = -1
        job_state = f'Unable to query job id {job_id}.'
    else:
        status = json.loads(resp.text)
        job_state = status['job_state']
        query_success = 1
    return query_success, job_state


def cancel_job(job_id, session, slurm_url):
    """Cancel slurm job and reports status."""
    cancel_success = 1
    resp = session.delete(f'{slurm_url}/job/{job_id}')
    if resp.status_code != 200:
        cancel_success = -1
        job_state = f"Unable to cancel job id {job_id}."
    else:
        job_state = "CANCELLED"
    return cancel_success, job_state


def submit_job(script, session, slurm_url):
    """Worker submits job-returns (job_id, job_state), or (-1, error)."""
    job_id = -1
    try:
        job_st = subprocess.check_output(['sbatch', '--parsable', script],
                                         stderr=subprocess.STDOUT)
        job_id = int(job_st)
    except subprocess.CalledProcessError as error:
        job_status = error.output.decode('utf-8')
        print(f'job_status is {job_status}')
    _, job_state = query_job(job_id, session, slurm_url)
    return job_id, job_state


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager."""

    def __init__(self, **kwargs):
        """Create a new Slurm Worker object."""
        self.slurm_socket = kwargs.get('slurm_socket', f'/tmp/slurm_{os.getlogin()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        # Note: Socket path is encoded, http request is not generally.
        self.slurm_url = f"http+unix://{encoded_path}/slurm/v0.0.35"

    def submit_task(self, task):
        """Worker builds & submits script."""
        build_success, task_script = write_script(task)
        if build_success:
            job_id, job_state = submit_job(task_script,
                                           self.session, self.slurm_url)
        else:
            job_id = build_success
            job_state = task_script
        return job_id, job_state

    def query_task(self, job_id):
        """Worker queries job; returns (1, job_state), or (-1, error_msg)."""
        query_success, job_state = query_job(job_id, self.session, self.slurm_url)
        return query_success, job_state

    def cancel_task(self, job_id):
        """Worker cancels job; returns (1, job_state), or (-1, error_msg)."""
        cancel_success = 1
        resp = self.session.delete(f'{self.slurm_url}/job/{job_id}')
        if resp.status_code != 200:
            cancel_success = -1
            job_state = f"Unable to cancel job id {job_id}."
        else:
            job_state = "CANCELLED"
        return cancel_success, job_state


crt = ContainerRuntimeInterface(CrtDriver)
