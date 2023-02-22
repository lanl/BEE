"""Abstract base class for crt_driver, the Container Runtime and drivers.

Builds text for job to run task in a Container
"""
from abc import ABC, abstractmethod


class ContainerRuntimeResult:
    """Result to be used for returning to the worker code."""

    def __init__(self, env_code, pre_commands, main_command, post_commands):
        """Construct the result."""
        self.env_code = env_code
        self.pre_commands = pre_commands
        self.main_command = main_command
        self.post_commands = post_commands


class CommandType:
    """Command types."""

    DEFAULT = 'default'
    ONE_PER_NODE = 'one-per-node'
    ENV = 'env'


class Command:
    """Command in a batch script."""

    def __init__(self, args, type_=CommandType.DEFAULT):
        """Construct the command."""
        self.args = args
        self.type = type_


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
