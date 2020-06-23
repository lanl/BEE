"""Slurm worker for work load management.

Using pyslurm for interface to slurm api where possible
For now build command for submitting batch job.
"""

import os
import sys
import string
import subprocess
import time
import json
import urllib
import requests_unixsocket

from beeflow.common.worker.worker import Worker

def get_ccname(image_path):
    """Strip directories & .tar, .tar.gz, tar.xz, or .tgz from image path."""
    name = os.path.basename(image_path).rsplit('.', 2)
    if name[-1] in ['gz', 'xz']:
        name.pop()
    if name[-1] in ['tar', 'tgz']:
        name.pop()
    name = '.'.join(name)
    return name


def build_text(task, template_file):
    """Build text for task script use template if it exists."""
    job_template = ''
    cc_text = ''
    docker = False
    if task.hints is not None:
        for hint in task.hints:
            req_class, key, value = hint
            if req_class == "DockerRequirement" and key == "dockerImageId":
                cc_tar = value
                cc_name = get_ccname(cc_tar)
                cc_text = 'module load charliecloud\n'
                cc_text += 'mkdir -p /tmp/USER\n'
                cc_text += 'ch-tar2dir ' + cc_tar + ' /tmp/USER\n'
                docker = True
    try:
        template_f = open(template_file, 'r')
        job_template = template_f.read()
        template_f.close()
    except OSError:
        print('\nNo job_template: creating a simple job template!')
        job_template = '#! /bin/bash\n#SBATCH\n'
    template = string.Template(job_template)
    job_text = template.substitute({'name': task.name, 'id': task.id})
    if docker:
        job_text = job_text + cc_text
        job_text = job_text.replace('USER', '$USER')
        job_text += 'ch-run /tmp/$USER/' + cc_name + ' -b $PWD -c /mnt/0 -- '
        job_text += ''.join(task.command) + '\n'
        job_text += 'rm -rf /tmp/$USER/' + cc_name + '\n'
    else:
        job_text += ''.join(task.command) + '\n'
    return job_text


def write_script(task):
    """Build task script; returns (1, filename) or (-1, error_message)."""
    # for now using fixed directory for task manager scripts and write them out
    # we may keep them in memory and only write for a debug or logging option
    # make directory if doesn't exist (now uses date, should be workflow name?)
    template_file = os.path.expanduser('~/.beeflow/worker/job.template')
    template_dir = os.path.dirname(template_file)
    script_dir = template_dir + '/workflow-' + time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(script_dir, exist_ok=True)
    task_text = build_text(task, template_file)
    task_script = script_dir + '/' + task.name + '-' + str(task.id) + '.sh'
    success = -1
    try:
        script_f = open(task_script, 'w')
        script_f.write(task_text)
        script_f.close()
        success = 1
    except subprocess.CalledProcessError as error:
        task_script = error.output.decode('utf-8')
    return success, task_script

def query_job(job_id, session, slurm_url):
    query_status = 1
    resp = session.get(f'{slurm_url}/job/{job_id}')
    if resp.status_code != 200:
        query_success = -1
        job_state = f"Unable to query job id {job_id}."
    else:
        status = json.loads(resp.text)
        job_state = status['job_state']
        query_success = 1
    return query_success, job_state


def cancel_job(job_id, session, slurm_url):
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
    _, job_state = query_job(job_id, session, slurm_url)
    return job_id, job_state


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager.

    Implements Worker using pyslurm, except submit_task uses subprocess.
    """
    def __init__(self, **kwargs):
        """Create a new Slurm Worker object.

        """

        self.slurm_socket = kwargs.get('slurm_socket',f'/tmp/slurm_{os.getlogin()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        self.slurm_url = f"http+unix://{encoded_path}/slurm/v0.0.35"
        print('Starting up with slurm_url:',self.slurm_url)

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
