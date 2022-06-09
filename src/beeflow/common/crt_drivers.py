"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text for job to run task in a Container
"""
from abc import ABC, abstractmethod
import os
from configparser import NoOptionError
import sys
from beeflow.common.config_driver import BeeConfig
from beeflow.common.build.build_driver import task2arg
from beeflow.cli import log
import beeflow.common.log as bee_logging

if len(sys.argv) >= 2:
    USERCONFIG = sys.argv[1]
    bc = BeeConfig(userconfig=USERCONFIG)
else:
    USERCONFIG = None
    bc = BeeConfig()

bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='crt_driver.log')


class ContainerRuntimeResult:
    """Result to be used for returning to the worker code."""

    def __init__(self, env_code, pre_commands, main_command, post_commands):
        """Construct the result."""
        self.env_code = env_code
        self.pre_commands = pre_commands
        self.main_command = main_command
        self.post_commands = post_commands


class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for generic container runtime."""

    @abstractmethod
    def run_text(self, task):
        """Create commands for job using the container runtime.

        Returns a tuple (pre-commands, main-command, post-commands).
        :param task: instance of Task
        :rtype tuple of (list of list of str, list of str, list of list of str)
        """

    @abstractmethod
    def build_text(self, userconfig, task):
        """Create text for builder pre-run using the container runtime.

        :param task: instance of Task
        :rtype string
        """


class CharliecloudDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Charliecloud as container runtime system.

    Builds the text for the task for using Charliecloud.
    """

    @staticmethod
    def get_ccname(image_path):
        """Strip directories & .tar, .tar.gz, tar.xz, or .tgz from image path."""
        name = os.path.basename(image_path).rsplit('.', 2)
        if name[-1] in ['gz', 'xz']:
            name.pop()
        if name[-1] in ['tar', 'tgz']:
            name.pop()
        name = '.'.join(name)
        return name

    @staticmethod
    def get_cc_options():
        """Retrieve Charlicloud options from configuration file."""
        try:
            chrun_opts = bc.userconfig.get('charliecloud', 'chrun_opts')
        except NoOptionError:
            chrun_opts = ''
        try:
            cc_setup = bc.userconfig.get('charliecloud', 'setup')
        except NoOptionError:
            cc_setup = ''
        return(chrun_opts, cc_setup)

    def run_text(self, task):
        """Build text for Charliecloud batch script."""
        # Read container archive path from config.
        try:
            if bc.userconfig['builder'].get('container_archive'):
                container_archive = bc.userconfig['builder'].get('container_archive')
            else:
                # Set container archive relative to bee_workdir if config does not specify
                log.warning('Invalid config file. container_archive not found in builder section.')
                container_archive = '/'.join([bee_workdir, 'container_archive'])
                log.warning(f'Assuming container_archive is {container_archive}')
        except KeyError:
            log.warning('Container is missing builder section')
            log.warning('Setting container archive relative to bee_workdir')
            container_archive = f'{bee_workdir}/container_archive'
        finally:
            self.container_archive = bc.resolve_path(container_archive)
            os.makedirs(self.container_archive, exist_ok=True)
            bc.modify_section('user', 'builder', {'container_archive': self.container_archive})
            log.info(f'Build container archive directory is: {self.container_archive}')
            log.info("Wrote deployed image root to user BeeConfig file.")

        task_container_name = None
        # The container runtime treats hints and requirements as dicts
        task.hints = dict(task.hints)
        task.requirements = dict(task.requirements)
        try:
            # Try to get Hints
            hint_container_name = task.hints['DockerRequirement']['containerName']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No container_name specified in task hints.
            hint_container_name = None
        try:
            # Try to get Requirements
            req_container_name = task.requirements['DockerRequirement']['containerName']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No container_name specified in task reqs.
            req_container_name = None

        # Prefer requirements over hints
        if req_container_name:
            task_container_name = req_container_name
        elif hint_container_name:
            task_container_name = hint_container_name

        baremetal = False
        if task_container_name is None:
            log.info('No container name provided.')
            log.info('Assuming another DockerRequirement is runtime target.')
            runtime_target_list = []
            # Harvest copyContainer if it exists.
            task_container_path = None
            try:
                # Try to get Hints
                hint_container_path = task.hints['DockerRequirement']['copyContainer']
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No container_path specified in task hints.
                hint_container_path = None
            try:
                # Try to get Requirements
                req_container_path = task.requirements['DockerRequirement']['copyContainer']
            except (KeyError, TypeError):
                # Task Requirements are not mandatory. No container_path specified in task reqs.
                req_container_path = None

            # Prefer requirements over hints
            if req_container_path:
                task_container_path = req_container_path
            elif hint_container_path:
                task_container_path = hint_container_path
            # If comes from copyContainer, harvest name from tarball.
            if task_container_path:
                task_container_path = os.path.basename(task_container_path).split('.')[0]
                runtime_target_list.append(task_container_path)
                log.info('Found copyContainer tarball, assuming this contains the container name.')

            # Harvest dockerPull if it exists
            task_addr = None
            try:
                # Try to get Hints
                hint_addr = task.hints['DockerRequirement']['dockerPull']
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No dockerPull image specified in task hints.
                hint_addr = None
            try:
                # Try to get Requirements
                req_addr = task.requirements['DockerRequirement']['dockerPull']
            except (KeyError, TypeError):
                # Task Requirements are not mandatory. No dockerPull image specified in task reqs.
                req_addr = None

            # Prefer requirements over hints
            if req_addr:
                task_addr = req_addr
            elif hint_addr:
                task_addr = hint_addr

            if task_addr:
                task_container_path = task_addr.replace('/', '%')
                runtime_target_list.append(task_container_path)
                log.info('Found dockerPull address, assuming this contains the container name.')
                if len(runtime_target_list) > 1:
                    raise RuntimeError(
                        'Too many container runtimes specified! Pick one per workflow step.'
                    )
            if len(runtime_target_list) == 0:
                log.warning('No containerName specified.')
                log.warning('Cannot be inferred from other DockerRequirements.')
                baremetal = True
            else:
                # Build container name from container path.
                task_container_name = runtime_target_list[0]
                log.info(f'Moving with expectation: {task_container_name} is the container target')

        if baremetal:
            return ContainerRuntimeResult(env_code='', pre_commands=[],
                                          main_command=[str(arg) for arg in task.command],
                                          post_commands=[])

        container_path = '/'.join([container_archive, task_container_name]) + '.tar.gz'
        log.info(f'Expecting container at {container_path}. Ready to deploy and run.')

        chrun_opts, cc_setup = self.get_cc_options()
        deployed_image_root = bc.userconfig.get('builder', 'deployed_image_root')

        command = ' '.join(task.command)
        cc_setup = cc_setup.split()
        env_code = [cc_setup] if cc_setup else []
        deployed_path = deployed_image_root + '/' + task_container_name
        pre_commands = [
            f'mkdir -p {deployed_image_root}\n'.split(),
            f'ch-convert -i tar -o dir {container_path} {deployed_path}\n'.split()
        ]
        main_command = f'ch-run --join {deployed_path} {chrun_opts} -- {command}\n'.split()
        post_commands = [
            f'rm -rf {deployed_path}\n'.split(),
        ]
        return ContainerRuntimeResult(env_code, pre_commands, main_command, post_commands)

    def build_text(self, userconfig, task):
        """Build text for Charliecloud batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n')
        return text


class SingularityDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Singularity as container runtime system.

    Builds the text for the task for using Singularity to test abstract class.
    """

    def run_text(self, task):
        """Build text for Singularity batch script."""
        # Make sure all commands are strings
        cmd_tasks = list(map(str, task.command))
        main_command = cmd_tasks
        if task.hints is not None:
            hints = dict(task.hints)
            try:
                img = hints['DockerRequirement']['copyContainer']
                argv = ['singularity', 'exec', img]
                argv.extend(cmd_tasks)
                main_command = argv
            except (KeyError, TypeError):
                pass
        return ContainerRuntimeResult(env_code='', pre_commands=[], main_command=main_command,
                                      post_commands=[])

    def build_text(self, userconfig, task):
        """Build text for Singularity batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n'
                )
        return text
# Ignore R0915: Too many statements is a personal preference. We exceed the default.
# Ignore W0201: Setting an attribute (ex self.blah) outside of __init__. Should fix this
#               eventually.
# Ignore W1202: Using fstring log formatting is not currently causing us problems.
# pylama:ignore=R0915,W0201,W1202
