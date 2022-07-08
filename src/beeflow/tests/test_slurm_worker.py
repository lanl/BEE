"""Tests of the Slurm worker."""
import uuid
import time
import subprocess
import os
from beeflow.common.config_driver import BeeConfig as bc


bc.init()


from beeflow.common.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.wf_data import Task


# Timeout (seconds) for waiting on tasks
TIMEOUT = 150
# Extra slurmrestd arguments. This may be something to take on the command line
SLURMRESTD_ARGS = ''
GOOD_TASK = Task(name='good-task', base_command=['ls', '/'], hints=[],
                 requirements=[], inputs=[], outputs=[], stdout='',
                 workflow_id=uuid.uuid4().hex)
BAD_TASK = Task(name='good-task', base_command=['/this/is/not/a/command'], hints=[],
                 requirements=[], inputs=[], outputs=[], stdout='',
                 workflow_id=uuid.uuid4().hex)


def wait_state(worker_iface, job_id, state):
    """Wait for Slurm to switch the job to another state."""
    time.sleep(1)
    n = 1
    last_state = worker_iface.query_task(job_id)
    while last_state == state:
        if n >= TIMEOUT:
            raise RuntimeError(f'job timed out, still in state {state}')
        time.sleep(1)
        n += 1
        last_state = worker_iface.query_task(job_id)
    return last_state


def setup_slurm_worker(fn):
    """Add a decorator to set up the worker interface."""
    def decorator():
        """Decorator function."""
        slurm_socket = f'/tmp/{uuid.uuid4().hex}.sock'
        bee_workdir = f'/tmp/{uuid.uuid4().hex}'
        os.mkdir(bee_workdir)
        proc = subprocess.Popen(f'slurmrestd {SLURMRESTD_ARGS} unix:{slurm_socket}', shell=True)
        time.sleep(1)
        worker_iface = WorkerInterface(worker=SlurmWorker, container_runtime='Charliecloud',
                                       slurm_socket=slurm_socket, bee_workdir=bee_workdir,
                                       job_template=bc.get('task_manager', 'job_template'))
        fn(worker_iface)
        time.sleep(1)
        proc.kill()
    return decorator


@setup_slurm_worker
def test_good_task(worker_iface):
    """Test submission of a good task."""
    job_id, last_state = worker_iface.submit_task(GOOD_TASK)
    assert last_state == 'PENDING'
    last_state = wait_state(worker_iface, job_id, 'PENDING')
    assert last_state == 'RUNNING'
    last_state = wait_state(worker_iface, job_id, 'RUNNING')
    assert last_state == 'COMPLETED'


@setup_slurm_worker
def test_bad_task(worker_iface):
    """Test submission of a bad task."""
    job_id, last_state = worker_iface.submit_task(BAD_TASK)
    assert last_state == 'PENDING'
    last_state = wait_state(worker_iface, job_id, 'PENDING')
    assert last_state == 'RUNNING'
    last_state = wait_state(worker_iface, job_id, 'RUNNING')
    assert last_state == 'FAILED'
