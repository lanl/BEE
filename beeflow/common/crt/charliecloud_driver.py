"""Driver for Charliecloud container runtime system.

Builds text needed to for job to run task in a Charliecloud Container
"""
import os

from beeflow.common.crt.crt_driver import ContainerRuntimeDriver


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
                        'mkdir -p /tmp/$USER\n',
                        'ch-tar2dir ', value, ' /tmp/$USER\n',
                        'ch-run /tmp/$USER/', name,
                        ' -b $PWD -c /mnt/0 -- ', command,
                        'rm -rf /tmp/$USER/', name, '\n'
                        ])
                    docker = True
            if not docker:
                text = command
        return text
