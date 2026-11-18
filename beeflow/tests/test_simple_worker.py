import os
import time
import uuid
import tempfile
import shutil
from beeflow.common.worker.simple_worker import SimpleWorker
from beeflow.common.object_models import Task

def test_simple_worker_kills_process_group():
    """Verify that cancelling a task kills all child processes."""
    # Create a temporary workdir for the test
    test_workdir = tempfile.mkdtemp()
    bee_workdir = tempfile.mkdtemp()
    try:
        # Create a task that spawns child processes
        workflow_id = uuid.uuid4().hex
        task = Task(
            name='test-process-group',
            base_command=['bash', '-c', 'sleep 100 & sleep 100 & wait'],
            hints=[],
            requirements=[],
            inputs=[],
            outputs=[],
            stdout=None,
            stderr=None,
            workflow_id=workflow_id,
            workdir=test_workdir
        )
        # Create SimpleWorker
        worker = SimpleWorker(
            bee_workdir=bee_workdir,
            container_runtime='Charliecloud'
        )
        # Submit the task
        job_id, job_state, job_info = worker.submit_task(task)
        assert job_state == 'RUNNING'
        # Wait for child processes to spawn
        time.sleep(1)
        # Count processes in the process group
        pgid = os.getpgid(job_id)
        processes_before = count_processes_in_group(pgid)
        # Should have at least 3 processes: main bash, 2 sleep children
        assert processes_before >= 3, f"Expected >= 3 processes, got {processes_before}"
        # Cancel the task
        cancel_state = worker.cancel_task(job_id, job_info=job_info)
        assert cancel_state == 'CANCELLED'
        # Wait a moment for signal propagation
        time.sleep(0.5)
        # Count processes after cancellation
        processes_after = count_processes_in_group(pgid)
        # All processes should be gone
        assert processes_after == 0, f"Expected 0 processes after cancel, got {processes_after}"
    finally:
        # Cleanup
        shutil.rmtree(test_workdir, ignore_errors=True)
        shutil.rmtree(bee_workdir, ignore_errors=True)


def count_processes_in_group(pgid):
    """Count the number of processes in a process group."""
    import subprocess
    try:
        # Use ps to find processes with matching PGID
        result = subprocess.run(
            ['ps', '-o', 'pgid=', '-A'],
            capture_output=True,
            text=True,
            check=True
        )
        # Count lines matching the PGID
        count = sum(1 for line in result.stdout.strip().split('\n')
                    if line.strip() == str(pgid))
        return count
    except subprocess.CalledProcessError:
        return 0