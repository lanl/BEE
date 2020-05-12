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
    """The ContainerRuntimeDriver where Charliecloud is the Container Runtime System.

    Builds the text for the task for using Charliecloud.
    """


    def container_text(self, task):
        cc_text = ''
        if task.hints is not None:
            for hint in task.hints:
                req_class, key, value = hint
                if req_class == "DockerRequirement" and key == "dockerImageId":
                    cc_name = get_ccname(value)
                    cc_text = 'module load charliecloud\n'
                    cc_text += 'mkdir -p /tmp/USER\n'
                    cc_text += 'ch-tar2dir ' + value + ' /tmp/USER\n'
                    cc_text = cc_text.replace('USER', '$USER')
                    cc_text += 'ch-run /tmp/$USER/' + cc_name + ' -b $PWD -c /mnt/0 -- '
                    cc_text += ''.join(task.command) + '\n'
                    cc_text += 'rm -rf /tmp/$USER/' + cc_name + '\n'
        print(f'cc_text {cc_text}')
        return cc_text
