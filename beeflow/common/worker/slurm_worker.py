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
import beeflow.common.worker.utils as worker_utils
from beeflow.common.worker.worker import (Worker, WorkerError)
from beeflow.common import validation
from beeflow.common.worker.utils import get_state_sacct
from beeflow.common.worker.utils import parse_key_val


log = bee_logging.setup(__name__)


class BaseSlurmWorker(Worker):
    """Base slurm worker code."""

    def __init__(self, default_account='', default_time_limit='', default_partition='',
            default_qos='', default_reservation='', **kwargs):
        """Initialize the base slurm worker."""
        super().__init__(**kwargs)
        self.default_account = default_account
        self.default_time_limit = default_time_limit
        self.default_partition = default_partition
        self.default_qos = default_qos
        self.default_reservation = default_reservation

    def get_task_requirements(self, task):
        """Get the task requirements."""

        requirements = {
                'nodes': task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1),
                'ntasks': task.get_requirement('beeflow:MPIRequirement', 'ntasks',
                    default=task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)),
                # Need to rethink the MPI version parameter
                'mpi_version': task.get_requirement('beeflow:MPIRequirement', 'mpiVersion',
                    default=''),
                'time_limit': validation.time_limit(task.get_requirement(
                    'beeflow:SlurmRequirement', 'timeLimit', default=self.default_time_limit)),
                'account': task.get_requirement('beeflow:SlurmRequirement', 'account',
                    default=self.default_account),
                'partition': task.get_requirement('beeflow:SlurmRequirement', 'partition',
                    default=self.default_partition),
                'qos': task.get_requirement('beeflow:SlurmRequirement', 'qos',
                    default=self.default_qos),
                'reservation': task.get_requirement('beeflow:SlurmRequirement', 'reservation',
                    default=self.default_reservation),
                'shell': task.get_requirement('beeflow:ScriptRequirement', 'shell',
                    default="/bin/bash"),
                'scripts_enabled': task.get_requirement('beeflow:ScriptRequirement', 'enabled',
                    default=False)
        }
        return requirements

    def build_sbatch_header(self, task, requirements):
        """Build the sbatch header."""
        stdout_path, stderr_path = self.resolve_stdout_stderr(task)
        header = [
                f'#!{requirements["shell"]}',
                f'#SBATCH --job-name={task.name}-{task.id}',
                f'#SBATCH --output={stdout_path}',
                f'#SBATCH --error={stderr_path}',
                f'#SBATCH -N {requirements["nodes"]}',
                f'#SBATCH -n {requirements["ntasks"]}',
                '#SBATCH --open-mode=append',
        ]
        if requirements['time_limit']:
            header.append(f'#SBATCH --time={requirements["time_limit"]}')
        if requirements['account']:
            header.append(f'#SBATCH --account {requirements["account"]}')
        if requirements['partition']:
            header.append(f'#SBATCH --partition {requirements["partition"]}')
        if requirements['qos']:
            header.append(f'#SBATCH --qos {requirements["qos"]}')
        if requirements['reservation']:
            header.append(f'#SBATCH --reservation {requirements["reservation"]}')
        # Return immediately on error
        if requirements["shell"] == "/bin/bash":
            header.append('set -e')
        return header

    def srun(self, script_lines, script_cmd, nodes):
        """Wrap a pre or post command with srun."""
        cmd_args = ' '.join(script_cmd.args)
        if script_cmd.type == 'one-per-node':
            script_lines.append(f'srun -N {nodes} -n {nodes} {cmd_args}')
        else:
            script_lines.append(f'srun {cmd_args}')

    def build_pre_commands(self, crt_res, script, requirements, pre_script=None):
        """Build the pre commands."""
        # Add pre-script commands if available
        for cmd in crt_res.pre_commands:
            self.srun(script, cmd, requirements['nodes'])
        if pre_script:
            script.extend(pre_script)
        return script

    def build_main_command(self, crt_res, requirements):
        """Build the main command."""
        mpi_arg = f'--mpi={requirements["mpi_version"]}' if requirements['mpi_version'] else ''
        # Removing this since everything is going to the workdir files now
        args = ' '.join(crt_res.main_command.args)
        return f'srun --nodes={requirements["nodes"]} {mpi_arg} {args}'

    def build_post_commands(self, crt_res, script, requirements, post_script=None):
        """Build post script commands."""
        for cmd in crt_res.post_commands:
            self.srun(script, cmd, requirements['nodes'])
        # Add post-script commands if available
        if post_script:
            script.extend(post_script)
        return script

    def build_text(self, task):
        """Build text for task script."""
        crt_res = self.crt.run_text(task)

        # Get task requirements
        requirements = self.get_task_requirements(task)

        pre_script, post_script = None, None
        if requirements['scripts_enabled']:
            # We use StringIO here to properly break the script up into lines with readlines
            pre_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                     'pre_script')).readlines()
            post_script = io.StringIO(task.get_requirement('beeflow:ScriptRequirement',
                                      'post_script')).readlines()
        # Build script sections
        script = self.build_sbatch_header(task, requirements)
        script.append(crt_res.env_code)

        # Pre commands
        script = self.build_pre_commands(crt_res, script, requirements, pre_script)

        # Main command
        script.append(self.build_main_command(crt_res, requirements))

        # Post commands
        script = self.build_post_commands(crt_res, script, requirements, post_script)

        return '\n'.join(script)

    def submit_job(self, script):
        """Worker submits job-returns (job_id, job_state)."""
        res = subprocess.run(['sbatch', '--parsable', script], text=True,  # pylint: disable=W1510
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

    def __init__(self, bee_workdir, **kwargs):
        """Create a new Slurmrestd Worker object."""
        openapi_version = worker_utils.get_slurmrestd_version()
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
        except requests.exceptions.JSONDecodeError as exc:
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
