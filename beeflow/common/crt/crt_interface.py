"""Mid-level interface for container runtime system.

Delegates the writing of the text for job script to an instance of a subclass 
of the abstract base class 'ContainerRuntimeDriver'. Default: 'CharliecloudDriver' class.
"""

from beeflow.common.crt.charliecloud_driver import CharliecloudDriver 


class ContainerRuntimeInterface:
    """Interface for the container runtime.

    Requires an implemented subclass of ContainerRuntimeDriver to function.
    """

    def __init__(self, crt_driver=CharliecloudDriver):
        """Initialize the container runtime interface with a runtime, 
           CharliecloudDriver by default.

        :param crt_driver: the container runtime driver (CharliecloudDriver by default)
        :type crt_driver: subclass of ContainerRuntimeDriver
        """
        self._crt_driver = crt_driver()

    def container_text(self, task):
        """Build text required for running the task using the container_runtime.

        :param task: instance of Task
        :rtype string
        """
        return self._crt_driver.container_text(task)
