"""Worker utility functions."""

from datetime import datetime as dt
import re
import shlex
import subprocess
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

def format_runtime(runtime):
    """Format the runtime in a human-readable way."""
    minutes, seconds = divmod(runtime, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def calc_runtime(job_state,job_info):
    """Calculate the runtime of a task when using slurmrestd."""
    start_time = job_info['start_time']['number']
    end_time = job_info['end_time']['number']

    cur_time = dt.now()
    cur_unix_time = int(cur_time.timestamp())

    if job_state == 'RUNNING' and start_time:
        runtime = format_runtime(cur_unix_time - start_time)
    elif job_state == 'COMPLETED' and start_time and end_time:
        runtime = format_runtime(end_time - start_time)
    else:
        runtime = '00:00:00'
    return runtime

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
