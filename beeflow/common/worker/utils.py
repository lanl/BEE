"""Worker utility functions."""

import re
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


def get_slurmrestd_version():
    """Get the newest slurmrestd version."""
    resp = subprocess.run(["slurmrestd", "-s", "list"], check=True, stderr=subprocess.PIPE,
                          text=True).stderr
    resp = resp.split("\n")
    # Confirm slurmrestd format is the same
    # If the slurmrestd list outputs has changed potentially something else has broken
    if "Possible OpenAPI plugins" not in resp[0]:
        print("Slurmrestd OpenAPI format has changed and things may break")
    api_versions = [line.split('/')[1] for line in resp[1:] if re.search(r"openapi/v\d+\.\d+\.\d+",
                                                                         line)]
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
