"""Worker utility functions."""

import subprocess
from beeflow.common.worker.worker import WorkerError


def get_state_sacct(job_id):
    """Get state from slurm using sacct command, used when other means fail."""
    job_state = "ZOMBIE"
    try:
        resp = subprocess.run(['sacct', '-n', '-j', str(job_id)], text=True, check=True,
                              stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        raise WorkerError(f'Failed to query job {job_id} using sacct') from exc
    else:
        job_state = resp.stdout.splitlines()[0].split()[5]
    finally:
        return job_state


def parse_key_val(pair):
    """Parse the key-value pair separated by '='."""
    i = pair.find('=')
    return (pair[:i], pair[i + 1:])
