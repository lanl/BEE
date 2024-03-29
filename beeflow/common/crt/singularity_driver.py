"""Singularity driver as the container runtime system for tasks.

Creates text for tasks using Singularity.
"""

from beeflow.common.crt.crt_driver import (ContainerRuntimeDriver, ContainerRuntimeResult, Command)
from beeflow.common.build.utils import task2arg


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
                argv = ['singularity', 'exec']
                if task.workdir is not None:
                    argv.extend(['--pwd', task.workdir])
                argv.append(img)
                argv.extend(cmd_tasks)
                main_command = argv
            except (KeyError, TypeError):
                pass
        main_command = Command(main_command)
        # Change to the working directory
        env_code = ''
        if task.workdir is not None:
            env_code = f'cd {task.workdir}\n'
        return ContainerRuntimeResult(env_code=env_code, pre_commands=[],
                                      main_command=main_command, post_commands=[])

    def build_text(self, userconfig, task):
        """Build text for Singularity batch script."""
        task_args = task2arg(task)
        text = (f'beeflow --build {userconfig} {task_args}\n'
                )
        return text
