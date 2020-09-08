"""LSF worker for workload management.

Builds command for submitting batch job.
"""

import os
import string
import subprocess

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


class LSFWorker(Worker):
    """The Worker for systems where LSF is the Workload Manager."""

    def __init__(self, **kwargs):
        """Create a new LSF Worker object."""
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
            self.template_text = ''

    def build_text(self, task):
        """Build text for task script use template if it exists."""
        template_text = self.template_text
        if template_text == '':
            template_text = '#! /bin/bash\n#BSUB\n'
        template = string.Template(template_text)
        job_text = template.substitute({'name': task.name, 'id': task.id})
        crt_text = self.crt.script_text(task)
        job_text += crt_text
        print(f'in build_text job_text returned {job_text}')
        return job_text

    def write_script(self, task):
        """Build task script; returns (1, filename) or (-1, error_message)."""
        success = -1
        if not self.crt.image_exists(task):
            return success, "dockerImageId is not a valid image"
        # for now using fixed directory for task manager scripts and write them out
        # we may keep them in memory and only write for a debug or logging option
        os.makedirs(f'{self.workdir}/worker', exist_ok=True)
        task_text = self.build_text(task)
        task_script = f'{self.workdir}/worker/{task.name}.sh'
        try:
            script_f = open(task_script, 'w')
            script_f.write(task_text)
            script_f.close()
            success = 1
        except subprocess.CalledProcessError as error:
            task_script = error.output.decode('utf-8')
        print(f'in write_script returning success {success} and task_script')
        return success, task_script

    @staticmethod
    def query_job(job_id):
        """Query lsf for job status."""
        print(f'in Query job {job_id}')
        query_success = 1
        job_state = 'PENDING'
        if job_state == 'RUNNING':
            job_state = 'COMPLETED'
        else:
            job_state = 'RUNNING'
        return query_success, job_state

    @staticmethod
    def cancel_job(job_id):
        """Cancel LSF job and reports status."""
        print('LSF cancel')
        cancel_success = 1
        job_state = "CANCELLED"
        return cancel_success, job_state

    def submit_job(self, script):
        """Worker submits job-returns (job_id, job_state), or (-1, error)."""
        print(f'LSF submit job script:\n {script}')
        job_id = 1
        job_state = 'PENDING'
        return job_id, job_state

    def submit_task(self, task):
        """Worker builds & submits script."""
        build_success, task_script = self.write_script(task)
        if build_success:
            job_id, job_state = self.submit_job(task_script)
        else:
            # build script error in task_script
            job_id = build_success
            job_state = task_script
        return job_id, job_state

    def query_task(self, job_id):
        """Worker queries job; returns (1, job_state), or (-1, error_msg)."""
        query_success, job_state = self.query_job(job_id)
        print(f'LSF query task {job_id}')
        return query_success, job_state

    def cancel_task(self, job_id):
        """Worker cancels job; returns (1, job_state), or (-1, error_msg)."""
        cancel_success = 1
        job_state = "CANCELLED"
        return cancel_success, job_state
