"""Worker utility functions."""

import subprocess
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
        job_id_idx = header.index('JobID')
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
