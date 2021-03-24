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
from beeflow.common.config_driver import BeeConfig
from beeflow.cli import log
import beeflow.common.log as bee_logging
from beeflow.common.build.build_driver import arg2task
import json
import sys

try:
    bc = BeeConfig(userconfig=sys.argv[1])
    my_args = sys.argv[2]
except IndexError:
    raise IndexError('build_interface must execute with 2 arguments.')

handler = bee_logging.save_log(bc, log, logfile='builder.log')
task = arg2task(my_args)
builder = CharliecloudBuildDriver(task)
builder.dockerPull()

class BuildInterfaceTM:
    """Interface for managing a build system with WFM.

    Requires an implemented subclass of BuildDriver (uses CharliecloudBuildDriver by default).
    """

    def __init__(self, build_driver=CharliecloudBuildDriver):
        """Initialize the build interface with a build driver.

        :param build_driver: the build system driver (CharliecloudBuildDriver by default)
        :type build_driver: subclass of BuildDriver
        """
        print("BuildInterface init:", self, build_driver)
