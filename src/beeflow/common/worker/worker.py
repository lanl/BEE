"""Abstract base class for worker, the workload manager."""

from abc import ABC, abstractmethod


class WorkerError(Exception):
    """Worker error class."""

    def __init__(self, msg):
        """Worker error constructor."""
        self.msg = msg


class Worker(ABC):
    """Worker interface for a generic workload manager."""

    @abstractmethod
    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state.

        :param task: instance of Task
        :rtype tuple (int, string)
        """

    @abstractmethod
    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype string
        """

    @abstractmethod
    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype string
        """
