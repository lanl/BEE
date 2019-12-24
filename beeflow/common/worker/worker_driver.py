""" Abstract base class for worker, the workload manager. """

from abc import ABC, abstractmethod

class Worker(ABC)
    """ Worker interface for a generic workload manager. """

    @abstractmethod
    def submit_job(self, script):
        """Workload managers to submit task script; returns job_id, job_state.

        :param task_script: task script strings
        :type task_script: list of strings
        :rtype tuple of ints
        """
        
    @abstractmethod
    def cancel_job(self, job_id):
        """Cancel job with job_id.

        :param job_id: job id on cluster, to be cancelled; returns job_state.
        :type job_id: integer
        :rtype int
        """

    @abstractmethod
    def query_job(self, job_id):
        """Queries state of job with job_id; returns job_state.
        
        :param job_id: job id to query for status.
        :type job_id: int
        :rtype string
        """


