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


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager."""

    def __init__(self, bee_workdir, **kwargs):
        """Create a new Slurm Worker object."""
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
        # Check for extra runner options
        self.runner_opts = kwargs['runner_opts'] if 'runner_opts' in kwargs else ''

    def build_text(self, task):
        """Build text for task script; use template if it exists."""
        workflow_path = f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'
        template_text = '#! /bin/bash\n'
        template_text += f'#SBATCH --job-name={task.name}-{task.id}\n'
        template_text += f'#SBATCH --output={workflow_path}/{task.name}-{task.id}.out\n'
        template_text += f'#SBATCH --error={workflow_path}/{task.name}-{task.id}.err\n'
        hints = dict(task.hints)
        # Add MPI requirements
        try:
            nodes = hints['beeflow:MPIRequirement']['nodes']
            template_text += f'#SBATCH -N {nodes}\n'
        except (KeyError, TypeError):
            pass
        try:
            tasks_per_node = hints['beeflow:MPIRequirement']['ntasks_per_node']
            template_text += f'#SBATCH --ntasks-per-node {tasks_per_node}\n'
        except (KeyError, TypeError):
            pass
        try:
            ntasks = hints['beeflow:MPIRequirement']['ntasks']
            template_text += f'#SBATCH -n {ntasks}\n'
        except (KeyError, TypeError):
            pass
        try:
            cpus_per_task = hints['beeflow:MPIRequirement']['cpus_per_task']
            template_text += f'#SBATCH --cpus-per-task {cpus_per_task}\n'
        except (KeyError, TypeError):
            pass
        template_text += self.template_text
        template = string.Template(template_text)
        job_text = template.substitute({'WorkflowID': task.workflow_id,
                                        'name': task.name,
                                        'id': task.id}
                                       )
        # Determine environment requirements
        env = []
        if 'beeflow:Environment' in hints:
            for key in hints['beeflow:Environment']:
                env.append('export {}="{}"\n'.format(key, hints['beeflow:Environment'][key]))
        job_text += ''.join(env)
        # Determine runner options
        runner_opts = []
        if self.runner_opts is not None:
            runner_opts.append(self.runner_opts)
        try:
            mpi_version = hints['beeflow:MPIRequirement']['version']
            runner_opts.append('--mpi={}'.format(mpi_version))
        except (KeyError, TypeError):
            pass
        runner_opts = ' '.join(runner_opts)
        crt_text = []
        commands = self.crt.run_text(task)
        for cmd in commands:
            if cmd.block is not None:
                crt_text.append(cmd.block)
                crt_text.append('\n')
            else:
                srun_opts = ''
                if cmd.one_per_node:
                    srun_opts = '--ntasks-per-node=1'
                crt_text.append('srun {} {} {}\n'.format(runner_opts, srun_opts, ' '.join(cmd.argv)))
        crt_text = ''.join(crt_text)
        job_text += crt_text
        return job_text

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
