
"""Simple Worker class for launching tasks on a system with no workload manager."""

import subprocess
import beeflow.common.worker.worker as worker


class SimpleWorker(worker.Worker):
    """Worker interface for a generic workload manager."""

    def __init__(self):
        """Simple worker class."""
        self.tasks = {}

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state.

        :param task: instance of Task
        :rtype tuple (int, string)
        """
        # TODO
        proc = subprocess.Popen(task.command.split())
        self.tasks[task.id] = proc
        return (task.id, 'PENDING')

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype string
        """
        # TODO
        self.tasks[job_id].kill()
        return 'CANCELLED'

    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype string
        """
        rc = self.tasks[job_id].poll()
        if rc is None:
            return 'RUNNING'
        elif rc == 0:
            return 'COMPLETED'
        else:
            return 'FAILED'
