"""Charliecloud driver as the container runtime system for tasks.

Creates text for tasks using Charliecloud.
"""

import os
from beeflow.common.crt.crt_driver import (ContainerRuntimeDriver, ContainerRuntimeResult)
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.build.build_driver import task2arg
from beeflow.cli import log
import beeflow.common.log as bee_logging


class CharliecloudDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Charliecloud as container runtime system.

    Creates the text for the task for using Charliecloud.
    """

    def __init__(self, bee_workdir):
        """Create CharliecloudDriver object."""
        # Setup logger
        bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='charliecloud_driver.log')
        # Retrieve Charlicloud options from configuration file.
        self.chrun_opts = bc.get('charliecloud', 'chrun_opts')
        self.cc_setup = bc.get('charliecloud', 'setup')
        # Read container archive path from config.
        container_archive = bc.get('builder', 'container_archive')
        self.container_archive = bc.resolve_path(container_archive)

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

    def run_text(self, task):
        """Create text for Charliecloud batch script."""
        os.makedirs(self.container_archive, exist_ok=True)
        log.info(f'Build container archive directory is: {self.container_archive}')

        use_container = None
        task_container_name = task.get_requirement('DockerRequirement', 'beeflow:containerName')

        baremetal = False
        if task_container_name is None:
            baremetal = True
            log.info('No beeflow:containerName provided.')
            runtime_target_list = []
            # Harvest beeflow:copyContainer if it exists.
            task_container_path = task.get_requirement('DockerRequirement',
                                                       'beeflow:copyContainer')
            if task_container_path:
                task_container_path = os.path.basename(task_container_path).split('.')[0]
                runtime_target_list.append(task_container_path)

            # Harvest dockerPull if it exists
            task_addr = task.get_requirement('DockerRequirement', 'dockerPull')
            if task_addr:
                task_container_path = task_addr.replace('/', '%')
                runtime_target_list.append(task_container_path)
                log.info(f'Found dockerPull path {task_container_path}. Using its container name.')
                if len(runtime_target_list) > 1:
                    raise RuntimeError(
                        'Too many container runtimes specified! Pick one per workflow step.'
                    )
            if len(runtime_target_list) == 0:
                log.warning('No beeflow:containerName specified.')
            else:
                baremetal = False
                # Build container name from container path.
                task_container_name = runtime_target_list[0]
                log.info(f'Moving w/expectation: {task_container_name} is the container target.')

            # Check for `beeflow:useContainer`
            use_container = task.get_requirement('DockerRequirement', 'beeflow:useContainer')
            if use_container:
                log.info(f'Found beeflow:useContainer option. Using container {use_container}')
                baremetal = False

        if baremetal:
            return ContainerRuntimeResult(env_code='', pre_commands=[],
                                          main_command=[str(arg) for arg in task.command],
                                          post_commands=[])

        if task_container_name:
            container_path = '/'.join([self.container_archive, task_container_name]) + '.tar.gz'

        # If use_container is specified, no copying is done, the file  path is used
        if use_container:
            task_container_name = self.get_ccname(use_container)
            container_path = os.path.expanduser(use_container)
        else:
            container_path = '/'.join([self.container_archive, task_container_name]) + '.tar.gz'

        log.info(f'Expecting container at {container_path}. Ready to deploy and run.')

        deployed_image_root = bc.get('builder', 'deployed_image_root')

        hints = dict(task.hints)
        mpi_opt = '--join' if 'beeflow:MPIRequirement' in hints else ''
        command = ' '.join(task.command)
        env_code = self.cc_setup if self.cc_setup else ''
        deployed_path = deployed_image_root + '/' + task_container_name
        pre_commands = [
            f'mkdir -p {deployed_image_root}\n'.split(),
            f'ch-convert -i tar -o dir {container_path} {deployed_path}\n'.split()
        ]
        main_command = f'ch-run {mpi_opt} {deployed_path} {self.chrun_opts} -- {command}\n'.split()
        post_commands = [
            f'rm -rf {deployed_path}\n'.split(),
        ]
        return ContainerRuntimeResult(env_code, pre_commands, main_command, post_commands)

    def build_text(self, userconfig, task):
        """Build text for Charliecloud batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n')
        return text
