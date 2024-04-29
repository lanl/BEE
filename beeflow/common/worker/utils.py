"""Worker utility functions."""

import subprocess


def get_state_sacct(job_id):
    """Get state from slurm using sacct command, used when other means fail."""
    resp = subprocess.run(['sacct', '-n', '-j', str(job_id)], text=True, check=True,
                          stdout=subprocess.PIPE)
    if resp.stdout:
        job_state = resp.stdout.splitlines()[0].split()[5]
    else:
        job_state = "ZOMBIE"
    return job_state


def parse_key_val(pair):
    """Parse the key-value pair separated by '='."""
    i = pair.find('=')
    return (pair[:i], pair[i + 1:])
