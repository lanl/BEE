"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text for job to run task in a Container
"""
from abc import ABC, abstractmethod
import os
from configparser import NoOptionError
from beeflow.common.config_driver import BeeConfig
from beeflow.common.build.build_driver import task2arg, arg2task
import sys
from beeflow.cli import log
import beeflow.common.log as bee_logging

if len(sys.argv) > 2:
    userconfig = sys.argv[1]
    bc = BeeConfig(userconfig=userconfig)
else:
    userconfig = None
    bc = BeeConfig()

bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='crt_driver.log')

class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for generic container runtime."""

    @abstractmethod
    def run_text(self, task):
        """Create text for job using the container runtime.

        :param task: instance of Task
        :rtype string
        """

    @abstractmethod
    def build_text(self, task):
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
                container_archive = '/'.join([bee_workdir,'container_archive'])
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
        if (req_container_name or hint_container_name) and (not hint_container_name):
            task_container_name = req_container_name
        elif hint_container_name:
            task_container_name = hint_container_name

        baremetal = False
        if task_container_name == None:
            log.info('No container name provided. Assuming copyContainer source is runtime target.')
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
            if (req_container_path or hint_container_path) and (not hint_container_path):
                task_container_path = req_container_path
            elif hint_container_path:
                task_container_path = hint_container_path

            if task_container_path == None:
                log.warning('No container specified, and cannot be inferred from copyContainer.')
                log.warning('Maybe you do not need a container, or try adding containerName or copyContainer.')
                baremetal = True
            else:
                # Build container name from container path.
                task_container_name = os.path.basename(task_container_path).split('.')[0]

                log.info('Moving with the expectation that {} is the runtime container target'.format(task_container_name))

        command = ''.join(task.command) + '\n'
        if baremetal:
            return command

        container_path = '/'.join([container_archive,task_container_name]) + '.tar.gz'
        log.info('Expecting container at {}. Ready to deploy and run.'.format(container_path))

        chrun_opts, cc_setup = self.get_cc_options()
        image_mntdir = bc.userconfig.get('charliecloud', 'image_mntdir')

        text = (f'{cc_setup}\n'
                f'mkdir -p {image_mntdir}\n'
                f'ch-tar2dir {container_path} {image_mntdir}\n'
                f'ch-run {image_mntdir}/{task_container_name} {chrun_opts} -- {command}'
                f'rm -rf {image_mntdir}/{task_container_name}\n'
                )
        return text

    def build_text(self, userconfig, task):
        """Build text for Charliecloud batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n'
                )
        return text

    def image_exists(self, task):
        """Check if image exists."""
        if task.hints is not None:
            for hint in task.hints:
                if hint.class_ == "DockerRequirement" and "dockerImageId" in hint.params.keys():
                    return os.access(hint.params["dockerImageId"], os.R_OK)
        return True


class SingularityDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Singularity as container runtime system.

    Builds the text for the task for using Singularity to test abstract class.
    """

    def run_text(self, task):
        """Build text for Singularity batch script."""
        if task.hints is not None:
            docker = False
            command = ''.join(task.command) + '\n'
            for hint in task.hints:
                if hint.class_ == "DockerRequirement" and "dockerImageId" in hint.params.keys():
                    text = ''.join([
                        'singularity exec ', hint.params["dockerImageId"],
                        ' ', command,
                        ])
                    docker = True
            if not docker:
                text = command
        return text

    def build_text(self, userconfig, task):
        """Build text for Singularity batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n'
                )
        return text

    def image_exists(self, task):
        """Check if image exists."""
        if task.hints is not None:
            for hint in task.hints:
                if hint.class_ == "DockerRequirement" and "dockerImageId" in hint.params.keys():
                    return os.access(hint.params["dockerImageId"], os.R_OK)
        return True
