"""Mid-level interface for managing a build system from WFM.

The WFM may request a Runtime Environment (RTE) that must be built. 
This RTE build should be considered a separate stage in the workflow.
The build_interface will access components of the build_driver and 
components of the gdb_interface as required.
"""

# from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
# from beeflow.common.build.container_drivers import CharliecloudBuildDriver,
#                                                    SingularityBuildDriver
from beeflow.common.build.container_drivers import CharliecloudBuildDriver


class BuildInterface:
    """Interface for managing a build system with WFM.

    Requires an implemented subclass of BuildDriver (uses CharliecloudBuildDriver by default).
    """

    def __init__(self, build_driver=CharliecloudBuildDriver):
        """Initialize the build interface with a build driver.

        :param build_driver: the build system driver (CharliecloudBuildDriver by default)
        :type build_driver: subclass of BuildDriver
        """
        print("BuildInterface init:", self, build_driver)
