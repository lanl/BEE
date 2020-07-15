"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text needed to for job to run task in a Container
"""
from abc import ABC, abstractmethod
import os


class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for generic container runtime."""

    @abstractmethod
    def script_text(self, task):
        """Build text for job using the container runtime.

        :param task: instance of Task
        :rtype string
        """
def get_ccname(image_path):
    """Strip directories & .tar, .tar.gz, tar.xz, or .tgz from image path."""
    name = os.path.basename(image_path).rsplit('.', 2)
    if name[-1] in ['gz', 'xz']:
        name.pop()
    if name[-1] in ['tar', 'tgz']:
        name.pop()
    name = '.'.join(name)
    return name


class CharliecloudDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Charliecloud as container runtime system.

    Builds the text for the task for using Charliecloud.
    """

    def script_text(self, task):
        if task.hints is not None:
            docker = False
            command = ''.join(task.command) + '\n'
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    name = get_ccname(value)
                    text = ''.join([
                        'module load charliecloud\n',
                        'mkdir -p /tmp\n',
                        'ch-tar2dir ', value, ' /tmp\n',
                        'ch-run /tmp/', name,
                        ' -b $PWD -c /mnt/0 -- ', command,
                        'rm -rf /tmp/', name, '\n'
                        ])
                    docker = True
            if not docker:
                text = command
        return text


class ChuckDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Charliecloud as runtime but prints 
       a message from Chuck. This is at temporary driver to show how the
       abstract class works.

    Builds the text for the task for using Charliecloud to test abstract class.
    """

    def script_text(self, task):
        if task.hints is not None:
            docker = False
            command = ''.join(task.command) + '\n'
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    name = get_ccname(value)
                    text = ''.join([
                        'echo Hello I am Chuck!\n'
                        'module load charliecloud\n',
                        'mkdir -p /tmp\n',
                        'ch-tar2dir ', value, ' /tmp\n',
                        'ch-run /tmp/', name,
                        ' -b $PWD -c /mnt/0 -- ', command,
                        'rm -rf /tmp/', name, '\n'
                        ])
                    docker = True
            if not docker:
                text = command
        return text