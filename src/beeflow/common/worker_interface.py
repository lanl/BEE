"""Mid-level interface for worker, a work load manager.

Delegates the actual work to an instance of a subclass of
the abstract base class 'Worker'. Default: 'SlurmWorker' class.
"""

from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.worker.lsf_worker import LSFWorker


class WorkerInterface:
    """Interface for monitoring and managing workloads and jobs.

    Requires an implemented subclass of Worker to function.
    """

    def __init__(self, worker=SlurmWorker, **kwargs):
        """Initialize the workload interface with a workload driver, SlurmWorker by default.

        :param worker: the work load driver (SlurmWorker by default)
        :type worker: subclass of Worker
        """
        self._worker = worker(**kwargs)

    def submit_task(self, task):
        """Worker builds script and submits task as job returns job_id, job_state.

        :param task: instance of Task
        :rtype: tuple (int, string)
        """
        # First prepare for the task (create necessary directories, etc.)
        self._worker.prepare(task)
        # Then submit it to the worker
        return self._worker.submit_task(task)

    def cancel_task(self, job_id):
        """Cancel job for task with job_id.

        :param job_id: job_id to be cancelled
        :type job_id: integer
        :rtype: string
        """
        return self._worker.cancel_task(job_id)

    def query_task(self, job_id):
        """Query state of job with job_id; returns job_state.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype: tuple (int, string)
        """
        return self._worker.query_task(job_id)
# Ignore W0611 module imported but unused error; unsure which workload scheduler will be needed
# pylama:ignore=W0611
