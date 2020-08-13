"""Abstract base class for worker, the workload manager."""

from abc import ABC, abstractmethod


class Worker(ABC):
    """Worker interface for a generic workload manager."""

    @abstractmethod
    def submit_task(self, task):
        """Worker submits task; returns id, state (or -1, error_message).

        :param task: instance of Task
        :rtype tuple (int, string)
        """

    @abstractmethod
    def cancel_task(self, job_id):
        """Cancel task with job_id; returns success/fail (1/-1) & job_state or error.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype tuple (int, string)
        """

    @abstractmethod
    def query_task(self, job_id):
        """Query job state; returns success/fail (1/-1), job_state or error message.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype tuple (int, string)
        """
