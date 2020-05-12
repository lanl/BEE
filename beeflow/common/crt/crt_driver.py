"""Abstract base class for crt_driver, the Container Runtime."""

from abc import ABC, abstractmethod


class ContainerRuntimeDriver(ABC):
    """ContainerRuntimeDriver interface for a generic container runtime system."""

    @abstractmethod
    def container_text(self, task):
        """Build text for job using the container runtime.

        :param task: instance of Task
        :rtype string
        """
