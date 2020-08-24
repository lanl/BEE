"""Mid-level interface for container runtime system.

Delegates the writing of the text for job script to an instance of a subclass
of the abstract base class 'ContainerRuntimeDriver'.
Default: 'CharliecloudDriver' class.
"""

from beeflow.common.crt.crt_drivers import CharliecloudDriver
from beeflow.common.crt.crt_drivers import SingularityDriver


class ContainerRuntimeInterface:
    """Interface for the container runtime.

    Requires an implemented subclass of ContainerRuntimeDriver to function.
    """

    def __init__(self, crt_driver=CharliecloudDriver):
        """Initialize the CRT interface with a runtime, CharliecloudDriver by default.

        :param crt_driver: container runtime driver (default: CharliecloudDriver)
        :type crt_driver: subclass of ContainerRuntimeDriver
        """
        self._crt_driver = crt_driver()

    def script_text(self, task):
        """Create text required to run the task using the container_runtime.

        :param task: instance of Task
        :rtype string
        """
        return self._crt_driver.script_text(task)

    def image_exists(self, task):
        """Check to see if the required container image exists.

        :param task: instance of Task
        :rtype boolean
        """
        return self._crt_driver.image_exists(task)
# Ignore module imported but unused error. No way to know which crt will be needed
# pylama:ignore=W0611
