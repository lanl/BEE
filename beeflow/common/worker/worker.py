"""Abstract base class for worker, the workload manager."""

# Disable W0511: This allows us to have TODOs in the code
# pylint:disable=W0511

from abc import ABC, abstractmethod
import os
from beeflow.common import log as bee_logging
from beeflow.common.crt_interface import ContainerRuntimeInterface


log = bee_logging.setup(__name__)


# Import all implemented container runtime drivers now
# No error if they don't exist
try:
    from beeflow.common.crt.charliecloud_driver import CharliecloudDriver
except ModuleNotFoundError:
    pass
try:
    from beeflow.common.crt.singularity_driver import SingularityDriver
except ModuleNotFoundError:
    pass


class WorkerError(Exception):
    """Worker error class."""

    def __init__(self, *args):
        """Construct a new worker error."""
        super(Exception, self).__init__()
        self.args = args


class Worker(ABC):
    """Worker interface for a generic workload manager."""

    def __init__(self, bee_workdir, **kwargs):
        """Load appropriate container runtime driver, based on configs in kwargs."""
        try:
            self.tm_crt = kwargs['container_runtime']
            crt_driver = CharliecloudDriver #default
            if self.tm_crt == 'Charliecloud':
                crt_driver = CharliecloudDriver
            elif self.tm_crt == 'Singularity':
                crt_driver = SingularityDriver
            self.crt = ContainerRuntimeInterface(crt_driver)
        except KeyError:
            log.warning("No container runtime specified in config; setting to Charliecloud.")
            self.tm_crt = 'Charliecloud'

        # Get BEE workdir from config file
        self.workdir = bee_workdir

    def task_save_path(self, task):
        """Return the task save path used for storing submission scripts output logs."""
        return f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'

    def write_script(self, task):
        """Build task script; returns filename of script."""
        task_text = self.build_text(task)
        task_script = f'{self.task_save_path(task)}/{task.name}-{task.id}.sh'
        with open(task_script, 'w', encoding='UTF-8') as script_f:
            script_f.write(task_text)
            script_f.close()
        return task_script

    def prepare(self, task):
        """Prepare for the task; create the task save directory, etc."""
        task_save_path = self.task_save_path(task)
        os.makedirs(task_save_path, exist_ok=True)

    @abstractmethod
    def build_text(self, task):
        """Build text for task script.

        :param task: task that we're building a script for
        :type task: Task
        :rtype: string
        """

    @abstractmethod
    def submit_task(self, task):
        """Worker submits task; returns job_id, job_state.

        :param task: instance of Task
        :rtype: tuple (int, string)
        """

    @abstractmethod
    def cancel_task(self, job_id):
        """Cancel task with job_id; returns job_state.

        :param job_id: to be cancelled
        :type job_id: integer
        :rtype: string
        """

    @abstractmethod
    def query_task(self, job_id):
        """Query job state for the task.

        :param job_id: job id to query for status.
        :type job_id: int
        :rtype: string
        """
