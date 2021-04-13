"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text for job to run task in a Container
"""
from abc import ABC, abstractmethod
import os
from configparser import NoOptionError
from beeflow.common.config_driver import BeeConfig
bc = BeeConfig()


class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for generic container runtime."""

    @abstractmethod
    def script_text(self, task):
        """Build text for job using the container runtime.

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

    def script_text(self, task):
        """Build text for Charliecloud batch script."""
        if task.hints is not None:
            docker = False
            command = ''.join(task.command) + '\n'
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    name = self.get_ccname(value)
                    chrun_opts, cc_setup = self.get_cc_options()
                    image_mntdir = bc.userconfig.get('charliecloud', 'image_mntdir')
                    text = (f'{cc_setup}\n'
                            f'mkdir -p {image_mntdir}\n'
                            #f'[ -d {image_mntdir}/{name} ] && chmod +w -R {image_mntdir}/{name}\n'
                            f'ch-tar2dir {value} {image_mntdir}\n'
                            f'ch-run {image_mntdir}/{name} {chrun_opts} -- {command}'
                            #f'[ -d {image_mntdir}/{name} ] && chmod +w -R {image_mntdir}/{name}\n'
                            f'rm -rf {image_mntdir}/{name}\n'
                            )
                    docker = True
            if not docker:
                text = command
        return text

    def image_exists(self, task):
        """Check if image exists."""
        if task.hints is not None:
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    return os.access(value, os.R_OK)
        return True


class SingularityDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Singularity as container runtime system.

    Builds the text for the task for using Singularity to test abstract class.
    """

    def script_text(self, task):
        """Build text for Singularity batch script."""
        if task.hints is not None:
            docker = False
            command = ''.join(task.command) + '\n'
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    text = ''.join([
                        'singularity exec ', value,
                        ' ', command,
                        ])
                    docker = True
            if not docker:
                text = command
        return text

    def image_exists(self, task):
        """Check if image exists."""
        if task.hints is not None:
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    return os.access(value, os.R_OK)
        return True
