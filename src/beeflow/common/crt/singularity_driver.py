"""Singularity driver as the container runtime system for tasks.

Creates text for tasks using Singularity.
"""

from beeflow.common.crt.crt_driver import (ContainerRuntimeDriver, ContainerRuntimeResult)
from beeflow.common.build.build_driver import task2arg


class SingularityDriver(ContainerRuntimeDriver):
    """The ContainerRuntimeDriver for Singularity as container runtime system.

    Creates the text for the task for using Singularity to test abstract class.
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