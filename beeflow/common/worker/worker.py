"""Abstract base class for worker, the workload manager."""

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
            if self.tm_crt == 'Charliecloud':
                crt_driver = CharliecloudDriver
            elif self.tm_crt == 'Singularity':
                crt_driver = SingularityDriver
            self.crt = ContainerRuntimeInterface(crt_driver)
        except KeyError:
            log.warning("No container runtime specified in config, proceeding with caution.")
            self.tm_crt = None
            crt_driver = None

        # Get BEE workdir from config file
        self.workdir = bee_workdir

    def task_save_path(self, task):
        """Return the task save path used for storing submission scripts output logs."""
        return f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'

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

# Ignore W0511: This allows us to have TODOs in the code
# pylama:ignore=W0511
