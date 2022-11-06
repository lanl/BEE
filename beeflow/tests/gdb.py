"""Helper functions for starting and stopping the GDB."""
import time
from beeflow.wf_manager.common import dep_manager
from beeflow.wf_manager.resources import wf_utils


def start():
    """Start the GDB."""
    # dep_manager.kill_gdb()
    # dep_manager.remove_current_run()
    try:
        dep_manager.create_image()
    except dep_manager.NoContainerRuntime:
        raise RuntimeError('Charliecloud is not installed') from None
    bolt_port = wf_utils.get_open_port()
    http_port = wf_utils.get_open_port()
    https_port = wf_utils.get_open_port()
    pid = dep_manager.start_gdb('/', bolt_port, http_port, https_port)
    time.sleep(10)
    return pid


def stop(pid):
    """Stop the GDB."""
    dep_manager.kill_gdb(pid)
    # dep_manager.remove_current_run()
