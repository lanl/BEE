"""Slurm worker for work load management.

Builds command for submitting batch job.
"""

import io
import subprocess
import json
import urllib
import getpass
import requests_unixsocket
import requests

from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)
from beeflow.common import validation
from beeflow.common.worker.utils import get_state_sacct
from beeflow.common.worker.utils import parse_key_val


log = bee_logging.setup(__name__)


class BaseSlurmWorker(Worker):
    """Base slurm worker code."""

    def __init__(self, default_account='', default_time_limit='', default_partition='', **kwargs):
        """Initialize the base slurm worker."""
        super().__init__(**kwargs)
        self.default_account = default_account
        self.default_time_limit = default_time_limit
        self.default_partition = default_partition

    def build_text(self, task):
        """Build text for task script."""
        task_save_path = self.task_save_path(task)
        crt_res = self.crt.run_text(task)
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
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=nodes)
        # Need to rethink the MPI version parameter
        mpi_version = task.get_requirement('beeflow:MPIRequirement', 'mpiVersion', default='')
        time_limit = task.get_requirement('beeflow:SchedulerRequirement', 'timeLimit',
                                          default=self.default_time_limit)
        time_limit = validation.time_limit(time_limit)
        account = task.get_requirement('beeflow:SchedulerRequirement', 'account',
                                       default=self.default_account)
        partition = task.get_requirement('beeflow:SchedulerRequirement',
                                         'partition',
                                         default=self.default_partition)

        shell = task.get_requirement('beeflow:ScriptRequirement', 'shell', default="/bin/bash")
        scripts_enabled = task.get_requirement('beeflow:ScriptRequirement', 'enabled',
                                               default=False)
        if scripts_enabled:
            # We use StringIO here to properly break the script up into lines with readlines
            pre_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                     'pre_script')).readlines()
            post_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                      'post_script')).readlines()
        # sbatch header
        script = [
            f'#!{shell}',
            f'#SBATCH --job-name={task.name}-{task.id}',
            f'#SBATCH --output={task_save_path}/{task.name}-{task.id}.out',
            f'#SBATCH --error={task_save_path}/{task.name}-{task.id}.err',
            f'#SBATCH -N {nodes}',
            f'#SBATCH -n {ntasks}',
            '#SBATCH --open-mode=append',
        ]
        if time_limit:
            script.append(f'#SBATCH --time={time_limit}')
        if account:
            script.append(f'#SBATCH -A {account}')
        if partition:
            script.append(f'#SBATCH -p {partition}')

        # Return immediately on error
        if shell == "/bin/bash":
            script.append('set -e')
        script.append(crt_res.env_code)

        def srun(script_lines, script_cmd):
            """Wrap a pre or post command with srun."""
            cmd_args = ' '.join(script_cmd.args)
            if script_cmd.type == 'one-per-node':
                script.append(f'srun -N {nodes} -n {nodes} {cmd_args}')
            else:
                script_lines.append(f'srun {cmd_args}')

        # Pre commands
        if scripts_enabled:
            for cmd in pre_script:
                script.append(cmd)

        for cmd in crt_res.pre_commands:
            srun(script, cmd)

        # Main command
        srun_args = ' '.join(main_command_srun_args)
        args = ' '.join(crt_res.main_command.args)
        if mpi_version:
            mpi_arg = f'--mpi={mpi_version}'
        else:
            mpi_arg = ''
        script.append(f'srun --nodes={nodes} {mpi_arg} {srun_args} {args}')

        # Post commands
        for cmd in crt_res.post_commands:
            srun(script, cmd)

        if scripts_enabled:
            for cmd in post_script:
                script.append(cmd)

        return '\n'.join(script)

    def write_script(self, task):
        """Build task script; returns filename of script."""
        task_text = self.build_text(task)

        task_script = f'{self.task_save_path(task)}/{task.name}-{task.id}.sh'
        with open(task_script, 'w', encoding='UTF-8') as script_f:
            script_f.write(task_text)
            script_f.close()
        return task_script

    def submit_job(self, script):
        """Worker submits job-returns (job_id, job_state)."""
        res = subprocess.run(['sbatch', '--parsable', script], text=True,  # noqa if we use check=True here, then we can't see stderr
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise WorkerError(f'Failed to submit job: {res.stderr}')
        job_id = int(res.stdout)
        job_state = self.query_task(job_id)
        return job_id, job_state

    def submit_task(self, task):
        """Worker builds & submits script."""
        task_script = self.write_script(task)
        job_id, job_state = self.submit_job(task_script)
        return job_id, job_state


class SlurmrestdWorker(BaseSlurmWorker):
    """Worker class for when slurmrestd is available."""

    def __init__(self, bee_workdir, openapi_version, **kwargs):
        """Create a new Slurmrestd Worker object."""
        super().__init__(bee_workdir=bee_workdir, **kwargs)
        # Pull slurm socket configs from kwargs (Uses getpass.getuser() instead
        # of os.getlogin() because of an issue with using getlogin() without a
        # controlling terminal)
        self.slurm_socket = kwargs.get('slurm_socket', f'/tmp/slurm_{getpass.getuser()}.sock')
        self.session = requests_unixsocket.Session()
        encoded_path = urllib.parse.quote(self.slurm_socket, safe="")
        # Note: Socket path is encoded, http request is not generally.
        self.slurm_url = f"http+unix://{encoded_path}/slurm/{openapi_version}"

    def query_task(self, job_id):
        """Worker queries job; returns job_state."""
        try:
            resp = self.session.get(f'{self.slurm_url}/job/{job_id}')
            if resp.status_code == 200:
                data = json.loads(resp.text)
                # Check for errors in the response
                check_slurm_error(data, f'Failed to query job {job_id}, slurm error.')
                # For some versions of slurm, the job_state isn't included on failure
                try:
                    job_state = data['jobs'][0]['job_state']
                except (KeyError, IndexError) as exc:
                    raise WorkerError(f'Failed to query job {job_id}') from exc
            else:
                # If slurmrestd does not find job make last attempt with sacct command
                job_state = get_state_sacct(job_id)
        except requests.exceptions.ConnectionError:
            job_state = "NOT_RESPONDING"
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


class SlurmCLIWorker(BaseSlurmWorker):
    """Slurm worker interface that uses the CLI."""

    def query_task(self, job_id):
        """Query job state for the task."""
        # Use scontrol since it gives a lot of useful info; may want to save info
        try:
            res = subprocess.run(['scontrol', 'show', 'job', str(job_id)],
                                 text=True, check=True, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            # If show job cannot find job get state using sacct (not same info)
            job_state = get_state_sacct(job_id)
        else:
            # Output is in a space-separated list of 'key=value' pairs
            pairs = res.stdout.split()
            key_vals = dict(parse_key_val(pair) for pair in pairs)
            job_state = key_vals['JobState']
        return job_state

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state."""
        try:
            subprocess.run(['scancel', str(job_id)], text=True, check=True)
        except subprocess.CalledProcessError:
            raise WorkerError(f'Failed to cancel job {job_id}') from None
        return 'CANCELLED'


class SlurmWorker(Worker):
    """Main slurm worker class."""

    def __init__(self, use_commands, **kwargs):
        """Construct the slurm worker.

        :param use_commands: whether or not to use Slurm's CLI
        :type use_commands: bool
        """
        super().__init__(**kwargs)
        if use_commands:
            self._inner = SlurmCLIWorker(**kwargs)
        else:
            self._inner = SlurmrestdWorker(**kwargs)

    def build_text(self, task):
        """Build text for task script; use template if it exists."""
        return self._inner.build_text(task)

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state."""
        return self._inner.submit_task(task)

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state."""
        return self._inner.cancel_task(job_id)

    def query_task(self, job_id):
        """Query job state for the task."""
        return self._inner.query_task(job_id)


def check_slurm_error(data, msg):
    """Check for an error in a Slurm response."""
    if 'errors' in data and data['errors']:
        err = data['errors'][0]
        desc = err['description']
        errmsg = err['error']
        raise WorkerError(f'{msg}: {errmsg} ({desc})')
