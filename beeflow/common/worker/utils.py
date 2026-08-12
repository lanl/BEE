"""Worker utility functions."""

import re
import shlex
import subprocess
import datetime
from packaging.version import Version

from beeflow.common.worker.worker import WorkerError
from beeflow.common import log as bee_logging


log = bee_logging.setup(__name__)


def get_state_sacct(job_id):
    """Get state from slurm using sacct command, used when other means fail."""
    log.info(f'Getting state with sacct for {job_id}')
    try:
        job_id = str(job_id)
        resp = subprocess.run(['sacct', '--parsable', '-j', job_id], text=True, check=True,
                              stdout=subprocess.PIPE)
        data = resp.stdout.splitlines()
        header = data[0]
        header = header.split('|')
        job_id_idx = header.index('JobId')
        rows = [row.split('|') for row in data[1:]]
        job_ids = [row[job_id_idx] for row in rows]
        info = rows[job_ids.index(job_id)]
        state_idx = header.index('State')
        return info[state_idx]
    except (subprocess.CalledProcessError, ValueError, KeyError) as exc:
        raise WorkerError(f'sacct query failed for job {job_id}') from exc


def write_submit_failure(stderr_path, message):
    """Record a job submission failure to the task's stderr file.

    Slurm only creates the task's .err file once a job starts running, so on a
    submit failure there is otherwise no record in the workflow directory of
    what went wrong. This writes the failure reason to the same path the task's
    stderr would have used, where the user would naturally look for it.

    Best-effort: a failure to write here must not mask the original submit
    error, so any OSError is logged rather than raised.
    """
    try:
        with open(stderr_path, 'a', encoding='utf-8') as err_file:
            err_file.write(f'Slurm job submission failed:\n{message}\n')
    except OSError as exc:
        log.warning(f'Could not record submit failure to {stderr_path}: {exc}')


def parse_key_val(pair):
    """Parse the key-value pair separated by '='."""
    i = pair.find('=')
    return (pair[:i], pair[i + 1:])


def get_slurmrestd_version():
    """Get the newest slurmrestd version."""
    resp = subprocess.run(["slurmrestd", "-d", "list"], check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True).stdout
    resp = resp.split("\n")
    # Confirm slurmrestd format is the same
    # If the slurmrestd list outputs has changed potentially something else has broken
    if "Possible data_parser plugins" not in resp[0]:
        print("Slurmrestd OpenAPI format has changed and things may break")
    api_versions = [line.split('/')[1] for line in resp[1:] if
            re.search(r"data_parser/v\d+\.\d+\.\d+", line)]
    # Sort the versions and grab the newest one
    newest_api = sorted(api_versions, key=Version, reverse=True)[0]
    return newest_api

def calculate_duration(start_time):
    """Calculates the duration of a task based on various start time formats."""
    now = datetime.datetime.now()
    if isinstance(start_time,int) and start_time>0:
        start_time = datetime.datetime.fromtimestamp(start_time)
    elif isinstance(start_time,str) and start_time != 'Unknown':
        start_time = datetime.datetime.fromisoformat(start_time)
    elif not isinstance(start_time,datetime.datetime):
        return '0:00:00'
    delta = start_time-now
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def format_start_time(start_time):
    """Formats the start time of a task.""" 
    if isinstance(start_time,(float,int)):
        if start_time == 0.0:
            return '0:00:00'
        start_time = datetime.datetime.fromtimestamp(start_time)
        if start_time.strftime('%Y-%m-%d %H:%M:%S') == '1969-12-31 17:00:00':
            start_time = '0:00:00'
        else:
            start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(start_time,str) and start_time != 'Unknown':
        start_time = datetime.datetime.fromisoformat(start_time)
        start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_time = '0:00:00'
    return start_time

def resolve_slurm_paths(job_id, task):
    """Replaces job id placeholder with actual job id."""
    if task.stdout is not None:
        task.stdout = task.stdout.replace("%j", str(job_id))
    if task.stderr is not None:
        task.stderr = task.stderr.replace("%j", str(job_id))

def parse_sbatch_output_error(sbatch_script):
    """Parses the stdout and stderr locations from an sbatch script."""

    stdout = None
    stderr = None

    # By default Slurm sets the output to be a file with this format in the working directory.
    default_output = "slurm-%j.out"
    for line in sbatch_script.splitlines():
        if not line.strip().startswith("#SBATCH"):
            continue
        # Just split on the first #SBATCH in case there's something weird
        args = line.split("#SBATCH", 1)[1]

        it = iter(shlex.split(args))
        for token in it:
            if token.startswith("--output="):
                stdout = token.split("=", 1)[1]
            elif token in ("--output", "-o"):
                stdout = next(it, None)
            elif token.startswith("--error="):
                stderr = token.split("=", 1)[1]
            elif token in ("--error", "-e"):
                stderr = next(it, None)
    if stdout is None:
        stdout = default_output
    if stderr is None:
        stderr = stdout
    return stdout, stderr
