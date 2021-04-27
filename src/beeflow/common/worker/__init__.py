"""Init file for the worker code."""
from .slurm_worker import SlurmWorker
from .lsf_worker import LSFWorker
from .simple_worker import SimpleWorker

from .worker import WorkerError


worker_classes = {
    'Slurm': SlurmWorker,
    'LSF': LSFWorker,
    'Simple': SimpleWorker,
}
