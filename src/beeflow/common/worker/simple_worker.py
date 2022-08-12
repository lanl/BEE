
"""Simple Worker class for launching tasks on a system with no workload manager."""

import subprocess

import os
from beeflow.common.worker.worker import Worker


class SimpleWorker(Worker):
    """Worker interface for system with no workload manager."""

    def __init__(self, container_runtime, **kwargs):
        """Create Simple worker object."""
        super().__init__(container_runtime=container_runtime, **kwargs)
        # This should be stored in Redis if possible
        self.tasks = {}

    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state.

        :param task: instance of Task
        :rtype: tuple (int, string)
        """
        script = self.build_text(task)
        script_path = os.path.join(self.task_save_path(task), f'{task.name}-{task.id}.sh')
        with open(script_path, 'w', encoding='UTF-8') as fp:
            fp.write(script)
        with subprocess.Popen(['/bin/sh', script_path]) as taskid:
            self.tasks[task.id] = taskid
        return (task.id, 'PENDING')

    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype: string
        """
        self.tasks[job_id].kill()
        return 'CANCELLED'

    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype: string
        """
        return_code = self.tasks[job_id].poll()
        # This assumes a standard returncode
        if return_code is None:
            return 'RUNNING'
        if return_code == 0:
            return 'COMPLETED'
        return 'FAILED'
