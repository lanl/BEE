""" Abstract base class for worker, the workload manager. """

from abc import ABC, abstractmethod


class Worker(ABC):
    """ Worker interface for a generic workload manager. """

    @abstractmethod
    def submit_job(self, script):
        """Worker submits task script; returns id, state, or 0, error.

        :param task_script: task script name
        :type task_script: string
        :rtype tuple (int, string)
        """

    @abstractmethod
    def cancel_job(self, job_id):
        """Cancel job with job_id; returns success (bool) & job_state or error.

        :param job_id: job id on cluster, to be cancelled; returns job_state.
        :type job_id: integer
        :rtype tuple (bool, string)
        """

    @abstractmethod
    def query_job(self, job_id):
        """Query job state; returns success(bool), job_state or error message.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype tuple (bool, string)
        """
