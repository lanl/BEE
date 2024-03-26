"""Mid-level interface for managing a build system from WFM.

The WFM may request a Runtime Environment (RTE) that must be built.
This RTE build should be considered a separate stage in the workflow.
The build_interface will access components of the build_driver and
components of the gdb_interface as required.
"""

# from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
# from beeflow.common.build.container_drivers import CharliecloudBuildDriver,
#                                                    SingularityBuildDriver
import sys
from subprocess import CalledProcessError
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import log as bee_logging
from beeflow.common.build.utils import arg2task, ContainerBuildError


log = bee_logging.setup(__name__)


def build_main(task):
    """Process build instructions - main code."""
    # The build driver treats Hint and Requirement objects as Dicts.
    task_local = task.copy()
    task_local.hints = dict(task_local.hints)
    task_local.requirements = dict(task_local.requirements)
    builder = CharliecloudBuildDriver(task_local)
    log.info('CharliecloudBuildDriver initialized')

    # Deque the next build instruction until empty or reach terminal case
    # ...catch the case where no build instructions are required.
    op_keys = ["build_op", "op_name", "op_priority", "op_terminal"]
    try:
        op_values = builder.exec_list.pop(0)
    except IndexError:
        log.info('No build instructions provided. Assuming this is ok...')
        op_values = [None, None, None, True]
    op_dict = dict(zip(op_keys, op_values))
    while op_dict["build_op"]:
        log.info(f'Executing build operation: {op_dict["op_name"]}')
        try:
            return_obj = op_dict["build_op"]()
            # Return objects will be successful subprocess or return code.
            try:
                return_code = return_obj.returncode
            except AttributeError:
                return_code = int(return_obj)
        except CalledProcessError as error:
            return_code = 1
            raise ContainerBuildError(
                f'There was a problem executing {op_dict["op_name"]}!'
            ) from error
        # Case 1: Not the last operation spec'd, but is a terminal operation.
        if op_dict["op_terminal"] and return_code == 0:
            op_values = [None, None, None, True]
            op_dict = dict(zip(op_keys, op_values))
            continue
        # Case 2: Go to next, or last operation spec'd.
        try:
            op_values = builder.exec_list.pop(0)
        except IndexError:
            op_values = [None, None, None, True]
        finally:
            op_dict = dict(zip(op_keys, op_values))


if __name__ == '__main__':
    try:
        bc.init(userconfig=sys.argv[1])
        my_args = sys.argv[2]
    except IndexError as exc:
        raise IndexError('build_interface must execute with 2 arguments.') from exc

    bee_workdir = bc.get('DEFAULT', 'bee_workdir')
    handler = bee_logging.save_log(bee_workdir=bee_workdir, log=log, logfile='build_interface.log')

    try:
        local_task = arg2task(my_args)
    except Exception as err:
        log.info(f'{err}')

    build_main(local_task)

# Ignore W0703: Catching generic exception isn't a problem if we just want a descriptive report
# Ignore C901: "'build_main' is too complex" - this function is just around 40 lines
# pylama:ignore=W0703,C901
