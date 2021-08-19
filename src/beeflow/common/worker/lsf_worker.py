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
    from beeflow.common.crt_drivers import CharliecloudDriver
except ModuleNotFoundError:
    pass
try:
    from beeflow.common.crt_drivers import SingularityDriver
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
            log.warning("No container runtime specified in config, proceeding with caution.")
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
        self.template_text = ''
        self.job_template = kwargs['job_template']
        if self.job_template:
            try:
                template_file = open(self.job_template, 'r')
                self.template_text = template_file.read()
                template_file.close()
                log.info(f'Jobs will use template: {self.job_template}')
            except ValueError as error:
                log.warning(f'Cannot open job template {self.job_template}, {error}')
                log.warning('Proceeding with Caution!')
            except FileNotFoundError:
                log.warning(f'Cannot find job template {self.job_template}')
                log.warning('Proceeding with Caution!')
            except PermissionError:
                log.warning(f'Permission error job template {self.job_template}')
                log.warning('Proceeding with Caution!')

        else:
            log.info('No template for jobs.')

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
        workflow_path = f'{self.workdir}/{task.workflow_id}/{task.name}-{task.id}'
        template_text = '#! /bin/bash\n'
        template_text += f'#BSUB -J {task.name}-{task.id}\n'
        template_text += f'#BSUB -o {workflow_path}/{task.name}-{task.id}.out\n'
        template_text += f'#BSUB -e {workflow_path}/{task.name}-{task.id}.err\n'
        template_text += self.template_text
        template = string.Template(template_text)
        job_text = template.substitute({'WorkflowID': task.workflow_id,
                                        'name': task.name,
                                        'id': task.id}
                                       )
        crt_text = self.crt.run_text(task)
        job_text += crt_text
        return job_text

    def write_script(self, task):
        """Build task script; returns filename of script."""
        script_dir = f'{self.workdir}/{task.workflow_id}/{task.name}-{task.id}'
        os.makedirs(script_dir, exist_ok=True)
        task_text = self.build_text(task)
        task_script = f'{script_dir}/{task.name}-{task.id}.sh'
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
        """Worker submits job-returns (job_id, job_state)."""
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
        """Worker cancels job, returns job_state."""
        subprocess.check_output(['bkill', str(job_id)], stderr=subprocess.STDOUT)
        job_state = "CANCELLED"
        return job_state
# Ignore R1732: Warnign about using open without "with' context. Seems like personal preference.
# pylama:ignore=R1732
