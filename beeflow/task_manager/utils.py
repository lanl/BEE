"""Task Manager utility functions."""
import os
from pathlib import Path
import re
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.db import tm_db
from beeflow.common.db import bdb
from beeflow.common import log as bee_logging
from beeflow.common import worker
from beeflow.common import paths
from beeflow.common.connection import Connection
from beeflow.common.worker_interface import WorkerInterface
import beeflow.common.worker.utils as worker_utils

log = bee_logging.setup(__name__)


def db_path():
    """Return the TM database path."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    return os.path.join(bee_workdir, 'tm.db')


def connect_db():
    """Connect to the TM database."""
    return bdb.connect_db(tm_db, db_path())


def worker_interface():
    """Load the worker interface."""
    wls = bc.get('DEFAULT', 'workload_scheduler')
    worker_class = worker.find_worker(wls)
    if worker_class is None:
        raise RuntimeError(f'Workload scheduler {wls}, not supported.\n'
                           + f'Please check {bc.userconfig_path()} and restart TaskManager.')
    # Get the parameters for the worker classes
    worker_kwargs = {
        'bee_workdir': bc.get('DEFAULT', 'bee_workdir'),
        'container_runtime': bc.get('task_manager', 'container_runtime'),
        # extra options to be passed to the runner (i.e. srun [RUNNER_OPTS] ... for Slurm)
        'runner_opts': bc.get('task_manager', 'runner_opts'),
    }
    # Job defaults
    for default_key in ['default_account', 'default_time_limit', 'default_partition',
                        'default_qos', 'default_reservation']:
        worker_kwargs[default_key] = bc.get('job', default_key)
    # Special slurm arguments
    if wls == 'Slurm':
        worker_kwargs['use_commands'] = bc.get('slurm', 'use_commands')
        worker_kwargs['slurm_socket'] = paths.slurm_socket()
        worker_kwargs['openapi_version'] = worker_utils.get_slurmrestd_version
    return WorkerInterface(worker_class, **worker_kwargs)


def wfm_url():
    """Return the url to the WFM."""
    # Saving this for whenever we need to run jobs across different machines
    # workflow_manager = 'bee_wfm/v1/jobs/'
    # #wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    # wfm_listen_port = wf_db.get_wfm_port()
    # return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}'
    return 'bee_wfm/v1/jobs/'


def wfm_resource_url(tag=""):
    """Get the full resource URL for access to the WFM."""
    return wfm_url() + str(tag)


def wfm_conn():
    """Get a new connection to the WFM."""
    return Connection(paths.wfm_socket())


class CheckpointRestartError(Exception):
    """Exception to be thrown on checkpoint-restart failure."""


def get_restart_file(task_checkpoint, task_workdir):
    """Find latest checkpoint file."""
    if 'file_regex' not in task_checkpoint:
        raise CheckpointRestartError('file_regex is required for checkpointing')
    if 'checkpoint_dir' not in task_checkpoint:
        raise CheckpointRestartError('checkpoint_dir is required for checkpointing')
    file_regex = task_checkpoint['file_regex']
    checkpoint_dir = Path(task_workdir, task_checkpoint['checkpoint_dir'])
    regex = re.compile(file_regex)
    try:
        checkpoint_files = [
            Path(checkpoint_dir, fname) for fname in os.listdir(checkpoint_dir)
            if regex.match(fname)
        ]
    except FileNotFoundError:
        raise CheckpointRestartError(
            f'Checkpoint checkpoint_dir ("{checkpoint_dir}") not found'
        ) from None
    checkpoint_files.sort(key=os.path.getmtime)
    try:
        checkpoint_file = checkpoint_files[-1]
        return str(checkpoint_file)
    except IndexError:
        raise CheckpointRestartError('Missing checkpoint file for task') from None


def check_sentinel_restart(task_checkpoint, task_workdir):
    """Check if sentinel file conditions indicate task should restart."""
    # If no sentinel_file_path defined, not using sentinel logic - proceed with restart
    if 'sentinel_file_path' not in task_checkpoint:
        return True
    sentinel_file_path = task_checkpoint['sentinel_file_path']
    restart_on_file_exists = task_checkpoint.get('restart_on_file_exists', True)
    # Build full path to sentinel file
    if os.path.isabs(sentinel_file_path):
        sentinel_path = Path(sentinel_file_path)
    else:
        # Resolve relative paths from task working directory
        sentinel_path = Path(task_workdir, sentinel_file_path)
    # Check if sentinel file exists
    file_exists = sentinel_path.exists()
    # Determine if restart should occur based on sentinel conditions:
    # - If restart_on_file_exists=True: restart when file EXISTS
    # - If restart_on_file_exists=False: restart when file DOES NOT exist
    should_restart = (file_exists and restart_on_file_exists) or \
                     (not file_exists and not restart_on_file_exists)
    log_msg = f'Sentinel check: file_exists={file_exists}, '
              f'restart_on_file_exists={restart_on_file_exists}, should_restart={should_restart}'
    log.info(log_msg)
    return should_restart
