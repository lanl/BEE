"""Background task code.

This code processes submitted tasks, monitors status, and sends info back to
the Workflow Manager.
"""
import traceback
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.task_manager import utils
from beeflow.common import log as bee_logging
from beeflow.common.build.utils import ContainerBuildError
from beeflow.common.build_interfaces import build_main
from beeflow.common.worker import WorkerError
from beeflow.wf_manager.models import TaskStateUpdateRequest

JOBS_MAX = 1000
log = bee_logging.setup(__name__)
jobs_limit = bc.get('task_manager', 'jobs_limit')
if not jobs_limit:
    jobs_limit = JOBS_MAX # pylint: disable=C0103 # not a constant
else:
    try:
        jobs_limit = int(jobs_limit)
    except ValueError:
        log.info(f'Value for jobs_limit in bee.conf not an integer, setting it to {JOBS_MAX}')
        jobs_limit = JOBS_MAX # pylint: disable=C0103 # not a constant
log.info(f'The number of jobs queued will be limited to {jobs_limit}.')

# States are based on https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
COMPLETED_STATES = {'UNKNOWN', 'COMPLETED', 'CANCELLED', 'FAILED', 'TIMEOUT'}

def resolve_environment(task):
    """Use build interface to create a valid environment.

    This will build and/or pull containers if necessary; it can take some time
    to run this step.
    """
    build_main(task)

def submit_task(db, worker, task):
    """Submit (or resubmit) a task."""
    try:
        has_container = task.get_full_requirement('DockerRequirement')
        if has_container:
            log.info(f'Resolving environment for task {task.name}')
            resolve_environment(task)
            log.info(f'Environment preparation complete for task {task.name}')
        job_id, job_state,job_info = worker.submit_task(task)
        log.info(f"Job Submitted '{task.name}' job_id: {job_id} job_state: {job_state}")
        # place job in queue to monitor
        db.job_queue.push(task=task, job_id=job_id, job_state=job_state)
    except ContainerBuildError as err:
        job_info = {}
        job_state = 'BUILD_FAIL'
        log.error(f'Failed to build container for {task.name}: {err}')
        log.error(f'{task.name} state: {job_state}')
    except Exception as err:  # pylint: disable=W0718 # we have to catch everything here
        # Set job state to failed
        job_info = {}
        job_state = 'SUBMIT_FAIL'
        log.error(f'Task Manager submit task {task.name} failed! \n {err}')
        log.error(f'{task.name} state: {job_state}')
        # Log the traceback information as well
        log.error(traceback.format_exc())
    # Send the initial state to WFM
    # update_task_state(task.id, job_state, metadata=task_metadata)
    return job_state,job_info


def submit_jobs(db):
    """Submit all jobs currently in submit queue to the workload scheduler."""
    worker = utils.worker_interface()
    while db.submit_queue.count() >= 1 and db.job_queue.count() < jobs_limit:
        # Single value dictionary
        task = db.submit_queue.pop()
        job_state,job_info = submit_task(db, worker, task)
        db.update_queue.push(task.workflow_id, task.id, job_state,\
                             task_info=None, metadata=job_info, output=None)


def update_jobs(db):
    """Check and update states of jobs in queue, remove completed jobs."""
    worker = utils.worker_interface()
    # Need to make a copy first
    job_q = list(db.job_queue)
    for job in job_q: # pylint: disable=R1702 # (7/5) nested blocks
        id_ = job.id
        task = job.task
        job_id = job.job_id
        job_state = job.job_state

        if job_state in COMPLETED_STATES:
            # Completed states don't change. Remove from the job queue and move to the next job.
            db.job_queue.remove_by_id(id_)
            continue

        try:
            new_job_state,job_info = worker.query_task(job_id)

        except WorkerError as err:
            log.warning(f'Failed to query job {job_id}: {err}')
            new_job_state = 'UNKNOWN'
            job_info={}

        # If state changes update the WFM
        if job_state != new_job_state:
            db.job_queue.update_job_state(id_, new_job_state)
            log.info(f"Job Updated '{task.name}' job_id: {job_id} job_state: {new_job_state}")
            if new_job_state in COMPLETED_STATES:
                # Check for checkpoint requirement
                task_checkpoint = task.get_full_requirement('beeflow:CheckpointRequirement')
                if task_checkpoint:
                    # Check if we should process this state based on restart_on_failure setting
                    should_process = False
                    restart_on_failure = task_checkpoint.get("restart_on_failure", True)
                    if restart_on_failure:
                        # Only process FAILED/TIMEOUT states
                        should_process = new_job_state in ('FAILED', 'TIMEOUT')
                    else:
                        # Process all completed states
                        should_process = True
                    if should_process:
                        log.info(f'Processing checkpoint/restart for {task.name} '
                                 f'in state {new_job_state}')
                        try:
                            # Check sentinel file conditions
                            should_restart = utils.check_sentinel_restart(task_checkpoint,
                                                                         task.workdir)
                            if should_restart:
                                # Harvest latest checkpoint file
                                checkpoint_file = utils.get_restart_file(task_checkpoint,
                                                                        task.workdir)
                                task_info = {'checkpoint_file': checkpoint_file, 'restart': True}
                                db.update_queue.push(task.workflow_id, task.id, new_job_state,
                                                    task_info=task_info, metadata=job_info,
                                                    output=None)
                            else:
                                # Sentinel conditions not met, don't restart
                                log.info(f'Sentinel conditions not met for {task.name}, '
                                         f'not restarting')
                                db.update_queue.push(task.workflow_id, task.id, new_job_state,
                                                    task_info=None, metadata=job_info, output=None)
                        except utils.CheckpointRestartError as err:
                            log.error(f'Checkpoint restart failed for '
                                      f'{task.name} ({task.id}): {err}')
                            db.update_queue.push(task.workflow_id, task.id, 'FAILED',
                                                task_info=None, metadata=job_info, output=None)
                    else:
                        # restart_on_failure=True but state is not FAILED/TIMEOUT
                        db.update_queue.push(task.workflow_id, task.id, new_job_state,
                                            task_info=None, metadata=job_info, output=None)
                else:
                    # No checkpoint requirement
                    db.update_queue.push(task.workflow_id, task.id, new_job_state,
                                        task_info=None, metadata=job_info, output=None)
            elif new_job_state in ('BOOT_FAIL', 'NODE_FAIL', 'OUT_OF_MEMORY', 'PREEMPTED'):
                # Don't update wfm, just resubmit
                log.info(f'Resubmitting task {task.name}')
                db.job_queue.remove_by_id(id_)
                job_state,job_info = submit_task(db, worker, task)
                db.update_queue.push(task.workflow_id, task.id, job_state,
                                    task_info=None,metadata=job_info,output=None)
            else:
		# Other state (e.g., PENDING)
                db.update_queue.push(task.workflow_id, task.id, new_job_state,
                                    task_info=None,metadata=job_info,output=None)

        if job_state in COMPLETED_STATES:
            db.job_queue.remove_by_id(id_)


def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    db = utils.connect_db()

    # Submit and update jobs
    submit_jobs(db)
    update_jobs(db)

    # Attempt to send a batch of task updates to the wfm, otherwise keep the
    # updates for later
    state_updates = TaskStateUpdateRequest(state_updates=db.update_queue.updates())
    conn = utils.wfm_conn()
    resp = conn.put(utils.wfm_resource_url("update/"), json=state_updates.model_dump())
    if resp.status_code == 200:
        # The workflow manager received the updates, so clear the queue
        db.update_queue.clear()
    else:
        log.info(resp)
        # Something bad happened so keep the udpates until the next round
        log.warning("WFM not responding when sending task updates.")
