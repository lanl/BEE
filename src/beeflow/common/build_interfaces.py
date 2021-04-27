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
    userconfig = sys.argv[1]
    bc = BeeConfig(userconfig=userconfig)
    my_args = sys.argv[2]
except IndexError:
    raise IndexError('build_interface must execute with 2 arguments.')

bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='builder.log')
task = arg2task(my_args)
builder = CharliecloudBuildDriver(task)

build_op, op_name, op_priority = builder.exec_list.pop(0)
while build_op:
    log.info('Executing build operation: "{}"'.format(op_name))
    build_op()
    try:
        build_op, op_name, op_priority = builder.exec_list.pop(0)
    except IndexError:
        log.info('Out of build instructions. Build operations complete.')
        build_op, op_name, op_priority = None, None, None
        
    

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
