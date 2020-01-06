"""Slurm worker for work load management.

Using pyslurm for interface to slurm api where possible.
For now build command for submitting batch job.
"""
import subprocess
import pyslurm

from beeflow.common.worker.worker import Worker


class SlurmWorker(Worker):
    """The Worker for systems where Slurm is the Work Load Manager.

    Implements Worker using pyslurm for slurm api except for submit_job uses subprocess.
    """

    def submit_job(self, script):
        """Worker submits task script; returns (job_id, job_state), or (0, error_message)."""
        try:
            job_st = subprocess.check_output(['sbatch', '--parsable', script],
                                             stderr=subprocess.STDOUT)
            job_id = int(job_st)
            job = pyslurm.job().find_id(job_id)[0]
            job_status = job_id, job['job_state']

        except subprocess.CalledProcessError as error:
            job_status = error.returncode, error.output.decode('utf-8')

        return job_status

    def query_job(self, job_id):
        """Worker queries job; returns (success(bool), job_state or error message(string))."""
        try:
            job = pyslurm.job().find_id(job_id)[0]
        except ValueError as error:
            query_success = False
            job_state = error.args[0]
        else:
            query_success = True
            job_state = job['job_state']
        return query_success, job_state

    def cancel_job(self, job_id):
        """Worker cancels job; returns (success(bool), job_state or error message(string))."""
        try:
            pyslurm.slurm_kill_job(job_id, 9, 0)
        except ValueError as error:
            cancel_success = False
            job_state = error.args[0]
        else:
            cancel_success = True
            job = pyslurm.job().find_id(job_id)[0]
            job_state = job['job_state']
        return cancel_success, job_state
