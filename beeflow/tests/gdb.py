"""Helper functions for starting and stopping the GDB."""
import time
from beeflow.wf_manager.common import dep_manager


def start():
    """Start the GDB."""
    dep_manager.kill_gdb()
    dep_manager.remove_current_run()
    try:
        dep_manager.create_image()
    except dep_manager.NoContainerRuntime:
        raise RuntimeError('Charliecloud is not installed') from None
    dep_manager.start_gdb()
    time.sleep(10)


def stop():
    """Stop the GDB."""
    dep_manager.kill_gdb()
    dep_manager.remove_current_run()
