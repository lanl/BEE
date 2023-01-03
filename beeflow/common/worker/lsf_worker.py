"""LSF worker for workload management.

Builds command for submitting batch job.
"""

import subprocess

from beeflow.common.worker.worker import Worker


class LSFWorker(Worker):
    """The Worker for systems where LSF is the Workload Manager."""

    def __init__(self, bee_workdir, **kwargs):
        """Create a new LSF Worker object."""
        super().__init__(bee_workdir, **kwargs)

        # Table of LSF states for translation to BEE states
        self.bee_states = {'PEND': 'PENDING',
                           'RUN': 'RUNNING',
                           'DONE': 'COMPLETED',
                           'QUIT': 'FAILED',
                           'PSUSP': 'PAUSED',
                           'USUSP': 'PAUSED',
                           'SSUSP': 'PAUSED'}
        # Check for extra runner options
        self.runner_opts = kwargs['runner_opts'] if 'runner_opts' in kwargs else ''

    def write_script(self, task):
        """Build task script; returns filename of script."""
        task_text = self.build_text(task)
        task_script = f'{self.task_save_path(task)}/{task.name}-{task.id}.sh'
        with open(task_script, 'w', encoding='UTF-8') as script_f:
            script_f.write(task_text)
            script_f.close()
        return task_script

    def query_job(self, job_id):
        """Query lsf for job status."""
        job_st = subprocess.check_output(['bjobs', '-aX', str(job_id), '-noheader'],
                                         stderr=subprocess.STDOUT)
        if 'not found' in str(job_st):
            raise Exception
        job_state = self.bee_states[job_st.decode().split()[2]]
        return job_state

    def submit_job(self, script):
        """Worker submits job-returns (job_id, job_state)."""
        job_st = subprocess.check_output(['bsub', script], stderr=subprocess.STDOUT)
        job_id = int(job_st.decode().split()[1][1:-1])
        job_state = self.query_job(job_id)
        return job_id, job_state

    def submit_task(self, task):
        """Worker builds & submits script."""
        task_script = self.write_script(task)
        job_id, job_state = self.submit_job(task_script)
        return job_id, job_state

    def query_task(self, job_id):
        """Worker queries job; returns job_state."""
        job_state = self.query_job(job_id)
        return job_state

    def cancel_task(self, job_id):
        """Worker cancels job, returns job_state."""
        subprocess.check_output(['bkill', str(job_id)], stderr=subprocess.STDOUT)
        job_state = "CANCELLED"
        return job_state
