"""Worker utility functions."""

import subprocess
from beeflow.common.worker.worker import WorkerError


def get_state_sacct(job_id):
    """Get state from slurm using sacct command, used when other means fail."""
    try:
        resp = subprocess.run(['sacct', '-n', '-j', str(job_id)], text=True, check=True,
                              stdout=subprocess.PIPE)
        if resp.stdout:
            job_state = resp.stdout.splitlines()[0].split()[5]
        else:
            job_state = "ZOMBIE"
    except subprocess.CalledProcessError as exc:
        job_state = "ZOMBIE"
        raise WorkerError(f'Failed to query job {job_id} with sacct') from exc
    finally:
        return job_state


def parse_key_val(pair):
    """Parse the key-value pair separated by '='."""
    i = pair.find('=')
    return (pair[:i], pair[i + 1:])
