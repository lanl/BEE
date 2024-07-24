"""Worker utility functions."""

import subprocess
from beeflow.common.worker.worker import WorkerError


def get_state_sacct(job_id):
    """Get state from slurm using sacct command, used when other means fail."""
    try:
        resp = subprocess.run(['sacct', '--parsable', '-j', str(job_id)], text=True, check=True,
                              stdout=subprocess.PIPE)
        data = resp.stdout.splitlines()
        header, info = data
        header = header.split('|')
        info = info.split('|')
        state_idx = header.index('State')
        return info[state_idx]
    except (subprocess.CalledProcessError, ValueError, KeyError) as exc:
        raise WorkerError(f'sacct query failed for job {job_id}') from exc


def parse_key_val(pair):
    """Parse the key-value pair separated by '='."""
    i = pair.find('=')
    return (pair[:i], pair[i + 1:])