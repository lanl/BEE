"""Mid-level interface for container runtime system.

Delegates the writing of the text for job script to an instance of a subclass
of the abstract base class 'ContainerRuntimeDriver'.
Default: 'CharliecloudDriver' class.
"""

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.crt.charliecloud_driver import CharliecloudDriver
from beeflow.common.crt.singularity_driver import SingularityDriver


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

    def run_text(self, task):
        """Create text required to run the task using the container_runtime.

        :param task: instance of Task
        :rtype: string
        """
        return self._crt_driver.run_text(task)

    def build_text(self, userconfig, task):
        """Create text required to build a task environment.

        :param task: instance of Task
        :param userconfig: path to userconfig file
        :rtype: string
        """
        return self._crt_driver.build_text(userconfig, task)
# Ignore module imported but unused error. No way to know which crt will be needed
# pylama:ignore=W0611
