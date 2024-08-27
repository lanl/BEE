"""Centralized path data for everything stored in the workdir."""
import os
from beeflow.common.config_driver import BeeConfig as bc


def workdir():
    """Return the workdir."""
    return bc.get('DEFAULT', 'bee_workdir')


def _sockdir():
    """Return the socket directory."""
    sockdir = os.path.join(workdir(), 'sockets')
    os.makedirs(sockdir, exist_ok=True)
    return sockdir


def beeflow_socket():
    """Return the socket for the beeflow daemon."""
    return os.path.join(_sockdir(), 'beeflow.sock')


def wfm_socket():
    """Get the socket path for the Workflow Manager."""
    return os.path.join(_sockdir(), 'wf_manager.sock')


def tm_socket():
    """Get the socket path for the Task Manager."""
    return os.path.join(_sockdir(), 'task_manager.sock')


def sched_socket():
    """Get the scheduler socket."""
    return os.path.join(_sockdir(), 'scheduler.sock')


def slurm_socket():
    """Get the slurm socket (for slurmrestd)."""
    return os.path.join(_sockdir(), 'slurmrestd.sock')


def log_path():
    """Return the main log path."""
    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    return os.path.join(bee_workdir, 'logs')


def log_fname(component):
    """Determine the log file name for the given component."""
    return os.path.join(log_path(), f'{component}.log')


def redis_root():
    """Get the redis root directory (create it if it doesn't exist)."""
    path = os.path.join(workdir(), 'redis')
    os.makedirs(path, exist_ok=True)
    return path


def redis_container():
    """Get the path to the unpacked Redis container."""
    return os.path.join(workdir(), 'deps/redis_container')


def redis_sock_fname():
    """Return the file name for the Redis socket."""
    return 'redis.sock'


def _celery_root():
    """Get the celery root directory (create it if it doesn't exist)."""
    path = os.path.join(workdir(), 'celery')
    os.makedirs(path, exist_ok=True)
    return path


def celery_config():
    """Return the celery config path."""
    return os.path.join(_celery_root(), 'celery.py')


def celery_db():
    """Return the celery db path."""
    return os.path.join(_celery_root(), 'celery.db')
