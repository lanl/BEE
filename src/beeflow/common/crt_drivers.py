"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text for job to run task in a Container
"""
from abc import ABC, abstractmethod
import os
from configparser import NoOptionError
import sys
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.build.build_driver import task2arg
from beeflow.cli import log
import beeflow.common.log as bee_logging

# The bc object must be created before importing other parts of BEE
# This is needed to generate Sphinx documentation
if not bc.ready():
    bc.init()

USERCONFIG = bc.userconfig_path()

bee_workdir = bc.get('DEFAULT', 'bee_workdir')
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
        :rtype: tuple of (list of list of str, list of str, list of list of str)
        """

    @abstractmethod
    def build_text(self, userconfig, task):
        """Create text for builder pre-run using the container runtime.

        :param task: instance of Task
        :rtype: string
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
        chrun_opts = bc.get('charliecloud', 'chrun_opts')
        cc_setup = bc.get('charliecloud', 'setup')
        return(chrun_opts, cc_setup)

    def run_text(self, task):
        """Build text for Charliecloud batch script."""
        # Read container archive path from config.
        container_archive = bc.get('builder', 'container_archive')
        self.container_archive = bc.resolve_path(container_archive)
        os.makedirs(self.container_archive, exist_ok=True)
        log.info(f'Build container archive directory is: {self.container_archive}')
        log.info("Wrote deployed image root to user BeeConfig file.")

        task_container_name = None
        # The container runtime treats hints and requirements as dicts
        hints = dict(task.hints)
        requirements = dict(task.requirements)
        try:
            # Try to get Hints
            hint_container_name = hints['DockerRequirement']['beeflow:containerName']
        except (KeyError, TypeError):
            # Task Hints are not mandatory. No container_name specified in task hints.
            hint_container_name = None
        try:
            # Try to get Requirements
            req_container_name = requirements['DockerRequirement']['beeflow:containerName']
        except (KeyError, TypeError):
            # Task Requirements are not mandatory. No container_name specified in task reqs.
            req_container_name = None

        # Prefer requirements over hints
        if req_container_name:
            task_container_name = req_container_name
        elif hint_container_name:
            task_container_name = hint_container_name

        baremetal = False 
        use_container = None
        if task_container_name is None:
            baremetal = True
            log.info('No container name provided.')
            log.info('Assuming another DockerRequirement is runtime target.')
            runtime_target_list = []
            # Harvest beeflow:copyContainer if it exists.
            task_container_path = None
            try:
                # Try to get Hints
                hint_container_path = hints['DockerRequirement']['beeflow:copyContainer']
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No container_path specified in task hints.
                hint_container_path = None
            try:
                # Try to get Requirements
                req_container_path = requirements['DockerRequirement']['beeflow:copyContainer']
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
                hint_addr = hints['DockerRequirement']['dockerPull']
            except (KeyError, TypeError):
                # Task Hints are not mandatory. No dockerPull image specified in task hints.
                hint_addr = None
            try:
                # Try to get Requirements
                req_addr = requirements['DockerRequirement']['dockerPull']
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
                log.warning('No beeflow:containerName specified.')
                log.warning('Cannot be inferred from other DockerRequirements.')
            else:
                baremetal = False
                # Build container name from container path.
                task_container_name = runtime_target_list[0]
                log.info(f'Moving with expectation: {task_container_name} is the container target')

            # Check for `beeflow:useContainer` (only in hints for now)
            try:
                use_container = hints['DockerRequirement']['beeflow:useContainer']
                log.info(f'Found beeflow:useContainer option. Using container {use_container}')
                baremetal = False
            except (KeyError, TypeError):
                pass

        if baremetal:
            return ContainerRuntimeResult(env_code='', pre_commands=[],
                                          main_command=[str(arg) for arg in task.command],
                                          post_commands=[])

        if task_container_name:
            container_path = '/'.join([container_archive, task_container_name]) + '.tar.gz'

        # If use_container is specified, then no copying is done and the file
        # path is used directly
        if use_container is not None:
            container_path = os.path.expanduser(use_container)
            tmp = os.path.basename(container_path)
            task_container_name = os.path.splitext(tmp)[0]
        else:
            container_path = '/'.join([container_archive, task_container_name]) + '.tar.gz'

        log.info(f'Expecting container at {container_path}. Ready to deploy and run.')

        chrun_opts, cc_setup = self.get_cc_options()
        deployed_image_root = bc.get('builder', 'deployed_image_root')

        mpi_opt = '--join' if 'beeflow:MPIRequirement' in hints else ''
        command = ' '.join(task.command)
        env_code = cc_setup if cc_setup else ''
        deployed_path = deployed_image_root + '/' + task_container_name
        pre_commands = [
            f'mkdir -p {deployed_image_root}\n'.split(),
            f'ch-convert -i tar -o dir {container_path} {deployed_path}\n'.split()
        ]
        main_command = f'ch-run {mpi_opt} {deployed_path} {chrun_opts} -- {command}\n'.split()
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
                img = hints['DockerRequirement']['beeflow:copyContainer']
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
