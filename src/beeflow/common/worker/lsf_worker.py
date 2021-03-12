"""LSF worker for workload management.

Builds command for submitting batch job.
"""

import os
import string
import subprocess

from beeflow.common.worker.worker import Worker
from beeflow.common.crt_interface import ContainerRuntimeInterface
from beeflow.cli import log
import beeflow.common.log as bee_logging

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

    def __init__(self, bee_workdir, **kwargs):
        """Create a new LSF Worker object."""
        # Setup logger
        bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='LSFWorker.log')

        # Load appropriate container runtime driver, based on configs in kwargs
        try:
            self.tm_crt = kwargs['container_runtime']
        except KeyError:
            log.warn("No container runtime specified in config, proceeding with caution.")
            self.tm_crt = None
            crt_driver = None
        finally:
            if self.tm_crt == 'Charliecloud':
                crt_driver = CharliecloudDriver
            elif self.tm_crt == 'Singularity':
                crt_driver = SingularityDriver
            self.crt = ContainerRuntimeInterface(crt_driver)

        # Get BEE workdir from config file
        self.workdir = bee_workdir

        # Get template for job, if option in configuration
        self.template_text = '#! /bin/bash\n#BSUB\n'
        self.job_template = kwargs['job_template']
        if self.job_template:
            try:
                template_file = open(self.job_template, 'r')
                self.template_text = template_file.read()
                template_file.close()
            except ValueError as error:
                log.warn(f'Cannot open job template {self.job_template}, {error}')
                log.warn('Proceeding with Caution!')
            except FileNotFoundError as error:
                log.warn(f'Cannot find job template {self.job_template}')
                log.warn('Proceeding with Caution!')
            except PermissionError as error:
                log.warn(f'Permission error job template {self.job_template}')
                log.warn('Proceeding with Caution!')

        # Table of LSF states for translation to BEE states
        self.bee_states = {'PEND': 'PENDING',
                           'RUN': 'RUNNING',
                           'DONE': 'COMPLETED',
                           'QUIT': 'FAILED',
                           'PSUSP': 'PAUSED',
                           'USUSP': 'PAUSED',
                           'SSUSP': 'PAUSED'}

    def build_text(self, task):
        """Build text for task script; use template if it exists."""
        template_text = self.template_text
        template = string.Template(template_text)
        job_text = template.substitute({'name': task.name, 'id': task.id})
        crt_text = self.crt.script_text(task)
        job_text += crt_text
        return job_text

    def write_script(self, task):
        """Build task script; returns filename of script."""
        if not self.crt.image_exists(task):
            raise Exception('dockerImageId not accessible or valid.')
        os.makedirs(f'{self.workdir}/worker', exist_ok=True)
        task_text = self.build_text(task)
        task_script = f'{self.workdir}/worker/{task.name}.sh'
        script_f = open(task_script, 'w')
        script_f.write(task_text)
        script_f.close()
        return task_script

    def query_job(self, job_id):
        """Query lsf for job status."""
        job_st = subprocess.check_output(['bjobs', '-aX', str(job_id), '-noheader'],
                                         stderr=subprocess.STDOUT)
        if 'not found' in str(job_st):
            raise Exception
        job_state = self.bee_states[job_st.decode().split()[2]]
        return job_state

    def submit_job(self, script):
        """Worker submits job-returns (job_id, job_state), or (-1, error)."""
        job_st = subprocess.check_output(['bsub', script], stderr=subprocess.STDOUT)
        job_id = int(job_st.decode().split()[1][1:-1])
        job_state = self.query_job(job_id)
        return job_id, job_state

    def submit_task(self, task):
        """Worker builds & submits script."""
        task_script = self.write_script(task)
        job_id, job_state = self.submit_job(task_script)
        return job_id, job_state

    def query_task(self, job_id):
        """Worker queries job; returns job_state."""
        job_state = self.query_job(job_id)
        return job_state

    def cancel_task(self, job_id):
        """Worker cancels job; job_state."""
        subprocess.check_output(['bkill', str(job_id)], stderr=subprocess.STDOUT)
        job_state = "CANCELLED"
        return job_state
