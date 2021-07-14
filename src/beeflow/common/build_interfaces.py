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
from subprocess import CalledProcessError

try:
    userconfig = sys.argv[1]
    bc = BeeConfig(userconfig=userconfig)
    my_args = sys.argv[2]
except IndexError:
    raise IndexError('build_interface must execute with 2 arguments.')

bee_workdir = bc.userconfig.get('DEFAULT', 'bee_workdir')
handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='builder.log')

try:
  task = arg2task(my_args)
  # The build interface treats Hint and Requirement objects as Dicts.
  task.hints = dict(task.hints)
  task.requirements = dict(task.requirements)
except Exception as e:
  log.info('{}'.format(e))

builder = CharliecloudBuildDriver(task)
log.info('CharliecloudBuildDriver initialized')

# Deque the next build instruction until empty or reach terminal case
# ...catch the case where no build instructions are required.
try:
    build_op, op_name, op_priority, op_terminal = builder.exec_list.pop(0)
except IndexError:
    log.info('No build instructions provided. Assuming this is ok...')
    build_op, op_name, op_priority, op_terminal = None, None, None, True

while build_op:
    log.info('Executing build operation: "{}"'.format(op_name))
    try:
        return_obj = build_op()
        # Return objects will be successful subprocess or return code.
        try:
            return_code = return_obj.returncode
        except AttributeError:
            return_code = int(return_obj)
    except CalledProcessError:
        return_code = 1
        log.warning('There was a problem executing {}, check relevant log for detail.'\
                    .format(op_name))
    # Case 1: Not the last operation spec'd, but is a terminal operation.
    if op_terminal and return_code==0:
        log.info('Reached terminal build case')
        build_op, op_name, op_priority, op_terminal = None, None, None, True
        continue
    # Case 2: Go to next, or last operation spec'd.
    try:
        build_op, op_name, op_priority, op_terminal = builder.exec_list.pop(0)
    except IndexError:
        build_op, op_name, op_priority, op_terminal = None, None, None, True
    
log.info('Out of build instructions. Build operations complete.')
