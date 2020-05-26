"""Abstract base class for crt_driver, the Container Runtime."""

from abc import ABC, abstractmethod


class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for generic container runtime."""

    @abstractmethod
    def script_text(self, task):
        """Build text for job using the container runtime.

        :param task: instance of Task
        :rtype string
        """
