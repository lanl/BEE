"""Init file for the worker package."""
import sys

from .slurm_worker import SlurmWorker
from .lsf_worker import LSFWorker
from .simple_worker import SimpleWorker


supported_workload_schedulers = {
    'Slurm': SlurmWorker,
    'LSF': LSFWorker,
    'Simple': SimpleWorker,
}


def find_worker(name):
    """Find the worker class or return None."""
    if name in supported_workload_schedulers:
        return supported_workload_schedulers[name]
    return None
