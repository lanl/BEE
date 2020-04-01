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

    def __init__(self, worker=SlurmWorker):
        """Initialize the workload interface with a workload driver, SlurmWorker by default.

        :param worker: the work load driver (SlurmWorker by default)
        :type worker: subclass of Worker
        """
        self._worker = worker()

    def submit_task(self, task, task_dict):
        """Workload manager to submit task as job returns job_id(-1 if error), job_state.

        :param task: instance of Task
        :rtype tuple (int, string)
        """
        return self._worker.submit_task(task, task_dict)

    def cancel_job(self, job_id):
        """Cancel job with job_id.

        :param job_id: job_id to be cancelled
        :type job_id: integer
        :rtype tuple (int, string)
        """
        return self._worker.cancel_job(job_id)

    def query_job(self, job_id):
        """Query state of job with job_id; returns success/fail (1/-1), job_state.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype tuple (int, string)
        """
        return self._worker.query_job(job_id)
