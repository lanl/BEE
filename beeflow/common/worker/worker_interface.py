"""Mid-level interface for worker, a work load manager

Delegate the actual work to an instance of a subclass of 
the abstract base class 'Worker'. Default: 'SlurmWorker' class.
Worker may be a configuration value in the future.

from beeflow.common.worker.slurm_driver import SlurmWorker

class WorkerInterface:
    """Interface for monitoring and managing workloads and jobs.

    Requires an implemented subclass of Worker to function.
    """

    def __init__(self, worker_driver=SlurmWorker):
        """Initialize the workload interface with a workload driver.

        :param worker: the work load driver (SlurmWorker by default)
        :type slurm_driver: subclass of Worker
        """

    def submit_job(self, task_script):
        """Workload manager to submit task script; returns job_id, job_state.

        :param task_script: task_script
        :type task_script: list of strings
        :rtype tuple of ints
        """
        
    def cancel_job(self, job_id):
        """Cancel job with job_id.

        :param job_id: job id on cluster, to be cancelled; returns job_state.
        :type job_id: integer
        :rtype int
        """

    def query_job(self, job_id):
        """Queries state of job with job_id; returns job_state.
        
        :param job_id: job id to query for status.
        :type job_id: int
        :rtype string
        """
