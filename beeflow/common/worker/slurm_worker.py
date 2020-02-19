"""Slurm worker for work load management.

Using pyslurm for interface to slurm api where possible
For now build command for submitting batch job.
"""
import os
import string
import subprocess
import time
import pyslurm

from beeflow.common.worker.worker import Worker


def build_text(task, template_file):
    """Build text for task scriptuse template if it exists."""
    job_template = ''
    try:
        template_f = open(template_file, 'r')
        job_template = template_f.read()
        template_f.close()
    except OSError as err:
        print("OS error: {0}".format(err))
        print('No job_template: creating a simple job template!')
        job_template = '#! /bin/bash\n#SBATCH\n'

    # substitute template & add the command (need to add requirements)
    template = string.Template(job_template)
    return template.substitute(task.__dict__) + ' '.join(task.command)


def write_script(task):
    """Build and write task script; returns (1, filename) or (-1, error_message)."""
    # for now using fixed directory for task manager scripts and write them out
    # we may keep them in memory and only write for a debug or logging option
    # make directory if it does not exist (for now use date, should be workflow name?)
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


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager.

    Implements Worker using pyslurm for slurm api except for submit_job uses subprocess.
    """

    def submit_job(self, script):
        """Worker submits job; returns (job_id, job_state), or (-1, error_message)."""
        job_id = -1
        try:
            job_st = subprocess.check_output(['sbatch', '--parsable', script],
                                             stderr=subprocess.STDOUT)
            job_id = int(job_st)
            job = pyslurm.job().find_id(job_id)[0]
            job_status = job['job_state']

        except subprocess.CalledProcessError as error:
            job_status = error.output.decode('utf-8')

        return job_id, job_status

    def submit_task(self, task):
        """Worker builds & submits task; returns (job_id, job_state), or (-1, error)."""
        build_success, task_script = write_script(task)
        if build_success:
            job_id, job_state = self.submit_job(task_script)
        else:
            job_id = build_success
            job_state = task_script
        return job_id, job_state

    def query_job(self, job_id):
        """Worker queries job; returns (1, job_state), or (-1(fail), error_message)."""
        try:
            job = pyslurm.job().find_id(job_id)[0]
        except ValueError as error:
            query_success = -1
            job_state = error.args[0]
        else:
            query_success = 1
            job_state = job['job_state']
        return query_success, job_state

    def cancel_job(self, job_id):
        """Worker cancels job; returns (1, job_state), or (-1(fail), error_message)."""
        try:
            pyslurm.slurm_kill_job(job_id, 9, 0)
        except ValueError as error:
            cancel_success = -1
            job_state = error.args[0]
        else:
            cancel_success = 1
            job = pyslurm.job().find_id(job_id)[0]
            job_state = job['job_state']
        return cancel_success, job_state
