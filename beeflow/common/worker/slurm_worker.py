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


def build_text(task, task_dict, template_file, docker=True):
    """Build text for task script use template if it exists."""
    job_template = ''
    # Use Charliecloud fix TODO some assumptions for now should be configurable
    # One of those assumptions is 'module load charliecloud'
    cc_text = ''
    #if task.hints.keys() and 'DockerRequirement' in task.hints.keys():
    if docker:
        #cc_tar = task.hints['DockerRequirement']['DockerImageId']
        cc_tar = '/usr/projects/beedev/toss-tiny-3-5.tar' 
        cc = os.path.basename(os.path.splitext(cc_tar)[0])
        cc_text = 'module load charliecloud\n'
        cc_text += 'mkdir -p /tmp/USER\n'
        cc_text += 'ch-tar2dir ' + cc_tar + ' /tmp/USER\n'
    try:
        template_f = open(template_file, 'r')
        job_template = template_f.read()
        template_f.close()
    except OSError:
        print('\nNo job_template: creating a simple job template!')
        job_template = '#! /bin/bash\n#SBATCH\n'
    template = string.Template(job_template)
    job_text = template.substitute(task_dict)
    if docker:
        job_text = job_text + cc_text
        job_text = job_text.replace('USER', '$USER')
        job_text += 'ch-run /tmp/$USER/' + cc + ' -b $PWD -c /mnt/0 -- '
        job_text += ''.join(task.command) + '\n'
        #print(f"Command is {job_text} cc is {cc}")
        job_text += 'rm -rf /tmp/$USER/' + cc + '\n'
    else:
        job_text += ' '.join(task.command) + '\n'
    return job_text


def write_script(task, task_dict):
    """Build task script; returns (1, filename) or (-1, error_message)."""
    # for now using fixed directory for task manager scripts and write them out
    # we may keep them in memory and only write for a debug or logging option
    # make directory if doesn't exist (now uses date, should be workflow name?)
    template_file = os.path.expanduser('~/.beeflow/worker/job.template')
    template_dir = os.path.dirname(template_file)
    script_dir = template_dir + '/workflow-' + time.strftime("%Y%m%d-%H%M%S")
    os.makedirs(script_dir, exist_ok=True)
    task_text = build_text(task, task_dict, template_file)
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


def submit_job(script):
    """Worker submits job-returns (job_id, job_state), or (-1, error)."""
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


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager.

    Implements Worker using pyslurm, except submit_task uses subprocess.
    """

    def submit_task(self, task, task_dict):
        """Worker builds & submits script."""
        build_success, task_script = write_script(task, task_dict)
        if build_success:
            job_id, job_state = submit_job(task_script)
        else:
            job_id = build_success
            job_state = task_script
        return job_id, job_state

    def query_job(self, job_id):
        """Worker queries job; returns (1, job_state), or (-1, error_msg)."""
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
        """Worker cancels job; returns (1, job_state), or (-1, error_msg)."""
        signal = 9
        batch_flag = 0
        cancel_success = 1
        if job_id > 0:
            try:
                pyslurm.slurm_kill_job(job_id, signal, batch_flag)
            except ValueError as error:
                cancel_success = -1
                job_state = error.args[0]
            else:
                job = pyslurm.job().find_id(job_id)[0]
                job_state = job['job_state']
        else:
            cancel_success = -1
            job_state = ('Cannot cancel job, invalid id ' + str(job_id) + '.')
        return cancel_success, job_state
