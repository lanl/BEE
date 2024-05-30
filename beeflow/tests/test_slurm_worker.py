"""Tests of the Slurm worker."""
import uuid
import shutil
import time
import subprocess
import os
import pytest
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.worker_interface import WorkerInterface
from beeflow.common.worker.worker import WorkerError
from beeflow.common.worker.slurm_worker import SlurmWorker
from beeflow.common.wf_data import Task


# Timeout (seconds) for waiting on tasks
TIMEOUT = 150
# Extra slurmrestd arguments. This may be something to take on the command line
OPENAPI_VERSION = bc.get('slurm', 'openapi_version')
GOOD_TASK = Task(name='good-task', base_command=['sleep', '3'], hints=[],
                 requirements=[], inputs=[], outputs=[], stdout='', stderr='',
                 workflow_id=uuid.uuid4().hex)
BAD_TASK = Task(name='bad-task', base_command=['/this/is/not/a/command'], hints=[],
                requirements=[], inputs=[], outputs=[], stdout='', stderr='',
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


@pytest.fixture(params=[True, False], ids=['slurm-commands', 'slurmrestd'])
def slurm_worker(request):
    """Slurm worker fixture."""
    slurm_socket = f'/tmp/{uuid.uuid4().hex}.sock'
    bee_workdir = os.path.expanduser(f'/tmp/{uuid.uuid4().hex}.tmp')
    os.mkdir(bee_workdir)
    proc = subprocess.Popen(f'slurmrestd -s openapi/{OPENAPI_VERSION} unix:{slurm_socket}',
                            shell=True)
    time.sleep(1)
    worker_iface = WorkerInterface(worker=SlurmWorker, container_runtime='Charliecloud',
                                   slurm_socket=slurm_socket, bee_workdir=bee_workdir,
                                   openapi_version=OPENAPI_VERSION,
                                   use_commands=request.param)
    yield worker_iface
    time.sleep(1)
    proc.kill()
    shutil.rmtree(bee_workdir)


@pytest.fixture
def slurmrestd_worker_no_daemon():
    """Fixture that creates the worker interface but not slurmrestd."""
    slurm_socket = f'/tmp/{uuid.uuid4().hex}.sock'
    bee_workdir = os.path.expanduser(f'/tmp/{uuid.uuid4().hex}.tmp')
    os.mkdir(bee_workdir)
    yield WorkerInterface(worker=SlurmWorker, container_runtime='Charliecloud',
                          slurm_socket=slurm_socket, bee_workdir=bee_workdir,
                          openapi_version=OPENAPI_VERSION,
                          use_commands=False)
    shutil.rmtree(bee_workdir)


def test_good_task(slurm_worker):
    """Test submission of a good task."""
    job_id, last_state = slurm_worker.submit_task(GOOD_TASK)
    if last_state == 'PENDING':
        last_state = wait_state(slurm_worker, job_id, 'PENDING')
    if last_state == 'RUNNING':
        last_state = wait_state(slurm_worker, job_id, 'RUNNING')
    if last_state == 'COMPLETING':
        last_state = wait_state(slurm_worker, job_id, 'COMPLETING')
    assert last_state == 'COMPLETED'


def test_bad_task(slurm_worker):
    """Test submission of a bad task."""
    job_id, last_state = slurm_worker.submit_task(BAD_TASK)
    if last_state == 'PENDING':
        last_state = wait_state(slurm_worker, job_id, 'PENDING')
    if last_state == 'RUNNING':
        last_state = wait_state(slurm_worker, job_id, 'RUNNING')
    if last_state == 'COMPLETING':
        last_state = wait_state(slurm_worker, job_id, 'COMPLETING')
    assert last_state == 'FAILED'


def test_query_bad_job_id(slurm_worker):
    """Test querying a bad job ID."""
    with pytest.raises(WorkerError):
        slurm_worker.query_task(888)


def test_cancel_good_job(slurm_worker):
    """Cancel a good job."""
    job_id, _ = slurm_worker.submit_task(GOOD_TASK)
    job_state = slurm_worker.cancel_task(job_id)
    assert job_state == 'CANCELLED'


def test_no_slurmrestd(slurmrestd_worker_no_daemon):
    """Test without running slurmrestd."""
    worker = slurmrestd_worker_no_daemon
    job_id, state = worker.submit_task(GOOD_TASK)
    assert state == 'NOT_RESPONDING'
    assert worker.query_task(job_id) == 'NOT_RESPONDING'
    assert worker.cancel_task(job_id) == 'NOT_RESPONDING'
# Ignoring R1732: This is not what we need to do with the Popen of slurmrestd above;
#                 using a with statement doesn't kill the process immediately but just
#                 waits for it to complete and slurmrestd never will unless we kill it.
# Ignoring E402: "module level import not at top of file" - this is required for
#                bee config
# Ignoring W0621: Redefinition of names is required for pytest
# pylama:ignore=R1732,E402,W0621
