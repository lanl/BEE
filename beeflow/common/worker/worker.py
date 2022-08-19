"""Abstract base class for worker, the workload manager."""

from abc import ABC, abstractmethod
import os
import jinja2
from beeflow.cli import log
from beeflow.common.crt_interface import ContainerRuntimeInterface


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

    def build_text(self, task):
        """Build text for task script; use template if it exists."""
        # workflow_path = f'{self.workdir}/workflows/{task.workflow_id}/{task.name}-{task.id}'
        task_save_path = self.task_save_path(task)
        crt_res = self.crt.run_text(task)
        requirements = dict(task.requirements)
        hints = dict(task.hints)
        job_text = self.template.render(
            task_save_path=task_save_path,
            task_name=task.name,
            task_id=task.id,
            workflow_id=task.workflow_id,
            env_code=crt_res.env_code,
            pre_commands=crt_res.pre_commands,
            main_command=crt_res.main_command,
            post_commands=crt_res.post_commands,
            requirements=requirements,
            hints=hints,
        )
        return job_text

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
