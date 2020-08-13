"""Mid-level interface for worker, a work load manager.

Delegates the actual work to an instance of a subclass of
the abstract base class 'Worker'. Default: 'SlurmWorker' class.
Worker may be a configuration value in the future.
"""

from beeflow.common.worker.slurm_worker import SlurmWorker


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
        """Workload manager submits task as job returns job_id(-1 = error), job_state.

        :param task: instance of Task
        :rtype tuple (int, string)
        """
        return self._worker.submit_task(task)

    def cancel_task(self, job_id):
        """Cancel job with job_id.

        :param job_id: job_id to be cancelled
        :type job_id: integer
        :rtype tuple (int, string)
        """
        return self._worker.cancel_task(job_id)

    def query_task(self, job_id):
        """Query state of job with job_id; returns success/fail (1/-1), job_state.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype tuple (int, string)
        """
        return self._worker.query_task(job_id)
