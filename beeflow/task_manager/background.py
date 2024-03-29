"""Background task code.

This code processes submitted tasks, monitors status, and sends info back to
the Workflow Manager.
"""
import traceback
import jsonpickle
from beeflow.task_manager import utils
from beeflow.common import log as bee_logging
from beeflow.common.build.utils import ContainerBuildError
from beeflow.common.build_interfaces import build_main


log = bee_logging.setup(__name__)


def update_task_state(workflow_id, task_id, job_state, **kwargs):
    """Informs the workflow manager of the current state of a task."""
    data = {'wf_id': workflow_id, 'task_id': task_id, 'job_state': job_state}
    if 'metadata' in kwargs:
        kwargs['metadata'] = jsonpickle.encode(kwargs['metadata'])

    if 'task_info' in kwargs:
        kwargs['task_info'] = jsonpickle.encode(kwargs['task_info'])

    data.update(kwargs)
    conn = utils.wfm_conn()
    resp = conn.put(utils.wfm_resource_url("update/"), json=data)
    if resp.status_code != 200:
        log.warning("WFM not responding when sending task update.")


def resolve_environment(task):
    """Use build interface to create a valid environment.

    This will build and/or pull containers if necessary; it can take some time
    to run this step.
    """
    build_main(task)


def submit_task(db, worker, task):
    """Submit (or resubmit) a task."""
    try:
        log.info(f'Resolving environment for task {task.name}')
        resolve_environment(task)
        log.info(f'Environment preparation complete for task {task.name}')
        job_id, job_state = worker.submit_task(task)
        log.info(f'Job Submitted {task.name}: job_id: {job_id} job_state: {job_state}')
        # place job in queue to monitor
        db.job_queue.push(task=task, job_id=job_id, job_state=job_state)
        # update_task_metadata(task.id, task_metadata)
    except ContainerBuildError as err:
        job_state = 'BUILD_FAIL'
        log.error(f'Failed to build container for {task.name}: {err}')
        log.error(f'{task.name} state: {job_state}')
    except Exception as err:  # noqa (we have to catch everything here)
        # Set job state to failed
        job_state = 'SUBMIT_FAIL'
        log.error(f'Task Manager submit task {task.name} failed! \n {err}')
        log.error(f'{task.name} state: {job_state}')
        # Log the traceback information as well
        log.error(traceback.format_exc())
    # Send the initial state to WFM
    # update_task_state(task.id, job_state, metadata=task_metadata)
    return job_state


def submit_jobs():
    """Submit all jobs currently in submit queue to the workload scheduler."""
    db = utils.connect_db()
    worker = utils.worker_interface()
    while db.submit_queue.count() >= 1:
        # Single value dictionary
        task = db.submit_queue.pop()
        job_state = submit_task(db, worker, task)
        update_task_state(task.workflow_id, task.id, job_state)


def update_jobs():
    """Check and update states of jobs in queue, remove completed jobs."""
    db = utils.connect_db()
    worker = utils.worker_interface()
    # Need to make a copy first
    job_q = list(db.job_queue)
    for job in job_q:
        id_ = job.id
        task = job.task
        job_id = job.job_id
        job_state = job.job_state
        new_job_state = worker.query_task(job_id)

        # If state changes update the WFM
        if job_state != new_job_state:
            db.job_queue.update_job_state(id_, new_job_state)
            if new_job_state in ('FAILED', 'TIMELIMIT', 'TIMEOUT'):
                # Harvest lastest checkpoint file.
                task_checkpoint = task.get_full_requirement('beeflow:CheckpointRequirement')
                log.info(f'state: {new_job_state}')
                log.info(f'TIMELIMIT/TIMEOUT task_checkpoint: {task_checkpoint}')
                if task_checkpoint:
                    try:
                        checkpoint_file = utils.get_restart_file(task_checkpoint, task.workdir)
                        task_info = {'checkpoint_file': checkpoint_file, 'restart': True}
                        update_task_state(task.workflow_id, task.id, new_job_state,
                                          task_info=task_info)
                    except utils.CheckpointRestartError as err:
                        log.error(f'Checkpoint restart failed for {task.name} ({task.id}): {err}')
                        update_task_state(task.workflow_id, task.id, 'FAILED')
                else:
                    update_task_state(task.workflow_id, task.id, new_job_state)
            # States are based on https://slurm.schedmd.com/squeue.html#SECTION_JOB-STATE-CODES
            elif new_job_state in ('BOOT_FAIL', 'NODE_FAIL', 'OUT_OF_MEMORY', 'PREEMPTED'):
                # Don't update wfm, just resubmit
                log.info(f'Task {task.name} in state {new_job_state}')
                log.info(f'Resubmitting task {task.name}')
                db.job_queue.remove_by_id(id_)
                job_state = submit_task(db, worker, task)
                update_task_state(task.workflow_id, task.id, job_state)
            else:
                update_task_state(task.workflow_id, task.id, new_job_state)

        if job_state in ('ZOMBIE', 'COMPLETED', 'CANCELLED', 'FAILED', 'TIMEOUT', 'TIMELIMIT'):
            # Remove from the job queue. Our job is finished
            db.job_queue.remove_by_id(id_)


def process_queues():
    """Look for newly submitted jobs and update status of scheduled jobs."""
    submit_jobs()
    update_jobs()
