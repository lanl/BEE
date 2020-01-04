""" Abstract base class for worker, the workload manager. """

from abc import ABC, abstractmethod

class Worker(ABC)
    """ Worker interface for a generic workload manager. """

    @abstractmethod
    def submit_job(self, script):
        """Workload managers to submit task script; returns job_id, job_state, or 0, error_message.

        :param task_script: task script name 
        :type task_script: string
        :rtype tuple (int, string) 
        """
        
    @abstractmethod
    def cancel_job(self, job_id):
        """Cancel job with job_id; returns cancel_success, job_state or error message.

        :param job_id: job id on cluster, to be cancelled; returns job_state.
        :type job_id: integer
        :rtype tuple (bool, string)
        """

    @abstractmethod
    def query_job(self, job_id):
        """Queries state of job with job_id; returns query_success, job_state or error message.
        
        :param job_id: job id to query for status.
        :type job_id: int
        :rtype tuple (bool, string)
        """

