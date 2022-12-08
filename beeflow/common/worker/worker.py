"""Abstract base class for worker, the workload manager."""

from abc import ABC, abstractmethod
import os
import jinja2
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

        # Get template for job
        self.job_template = kwargs['job_template']
        if self.job_template:
            # Make sure that the file exists and is readable
            try:
                with open(self.job_template, 'r', encoding='UTF-8') as template_file:
                    template_file.read()
                log.info(f'Jobs will use template: {self.job_template}')
            except ValueError as error:
                raise RuntimeError(f'Cannot open {self.job_template}, {error}') from error
            except FileNotFoundError as exc:
                raise RuntimeError(f'Cannot find job template {self.job_template}') from exc
            except PermissionError as error:
                raise RuntimeError(f'Permission error {self.job_template}') from error
        else:
            raise RuntimeError('No job_template found for the worker class')

    @property
    def template(self):
        """Load the template file."""
        with open(self.job_template, encoding='UTF-8') as fp:
            return jinja2.Template(fp.read())

    def task_save_path(self, task):
        """Return the task save path used for storing submission scripts output logs."""
        return f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'

    def prepare(self, task):
        """Prepare for the task; create the task save directory, etc."""
        task_save_path = self.task_save_path(task)
        os.makedirs(task_save_path, exist_ok=True)

    @abstractmethod
    def build_text(self, task):
        """Build text for task script; use template if it exists.

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

# Ignore W0511: Ignore TODOs since we will want to address this later.
# pylama:ignore=W0511
