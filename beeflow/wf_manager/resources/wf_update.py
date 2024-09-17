"""Contains the workflow update REST endpoint."""

import os
import json
import shutil
import subprocess
import time
import jsonpickle

from flask import make_response, jsonify
from flask_restful import Resource, reqparse
from beeflow.wf_manager.resources import wf_utils
from beeflow.common import log as bee_logging

from beeflow.common.db import wfm_db
from beeflow.common.db.bdb import connect_db
from beeflow.common.config_driver import BeeConfig as bc

log = bee_logging.setup(__name__)
db_path = wf_utils.get_db_path()


def archive_workflow(db, wf_id, final_state=None):
    """Archive a workflow after completion."""
    # Archive Config
    workflow_dir = wf_utils.get_workflow_dir(wf_id)
    shutil.copyfile(os.path.expanduser("~") + '/.config/beeflow/bee.conf',
                    workflow_dir + '/' + 'bee.conf')

    wf_state = f'Archived/{final_state}' if final_state is not None else 'Archived'
    db.workflows.update_workflow_state(wf_id, wf_state)
    wf_utils.update_wf_status(wf_id, wf_state)

    bee_workdir = wf_utils.get_bee_workdir()
    archive_dir = os.path.join(bee_workdir, 'archives')
    os.makedirs(archive_dir, exist_ok=True)
    archive_path = f'../archives/{wf_id}.tgz'
    # We use tar directly since tarfile is apparently very slow
    workflows_dir = wf_utils.get_workflows_dir()
    subprocess.call(['tar', '-czf', archive_path, wf_id], cwd=workflows_dir)
    remove_wf_dir = bc.get('DEFAULT', 'delete_completed_workflow_dirs')
    if remove_wf_dir:
        log.info('Removing Workflow Directory')
        wf_utils.remove_wf_dir(wf_id)


def archive_fail_workflow(db, wf_id):
    """Archive and fail a workflow."""
    archive_workflow(db, wf_id, final_state='Failed')


def set_dependent_tasks_dep_fail(db, wfi, wf_id, task):
    """Recursively set all dependent task states of this task to DEP_FAIL."""
    # List of tasks whose states have already been updated
    set_tasks = [task]
    while len(set_tasks) > 0:
        dep_tasks = wfi.get_dependent_tasks(set_tasks.pop())
        for dep_task in dep_tasks:
            wfi.set_task_state(dep_task, 'DEP_FAIL')
            db.workflows.update_task_state(dep_task.id, wf_id, 'DEP_FAIL')
        set_tasks.extend(dep_tasks)


class WFUpdate(Resource):
    """Class to interact with an existing workflow."""

    def __init__(self):
        """Set up arguments."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('state_updates', type=str, location='json', required=True)

    def put(self):
        """Do a batch update of task states from the task manager."""
        db = connect_db(wfm_db, db_path)
        data = self.reqparse.parse_args()
        state_updates = jsonpickle.decode(data['state_updates'])

        for state_update in state_updates:
            self.update_task_state(state_update, db)

        return make_response(jsonify(status=('Tasks updated successfully')), 200)

    def handle_metadata(self, state_update, task, wfi):
        """Handle metadata for a task update."""
        bee_workdir = wf_utils.get_bee_workdir()

        # Get metadata from update if available
        if state_update.metadata is not None:
            old_metadata = wfi.get_task_metadata(task)
            old_metadata.update(state_update.metadata)
            wfi.set_task_metadata(task, old_metadata)

        # Get output from the task
        if state_update.output is not None:
            fname = f'{wfi.workflow_id}_{task.id}_{int(time.time())}.json'
            task_output_path = os.path.join(bee_workdir, fname)
            with open(task_output_path, 'w', encoding='utf8') as fp:
                json.dump(state_update.output, fp, indent=4)

    def handle_checkpoint_restart(self, state_update, task, wfi, db):
        """Handle checkpoint restart for a task update.

        Returns True if a checkpoint-restart was done, else False (indicating
        that more state handling is necessary).
        """
        if state_update.task_info is not None:
            checkpoint_file = state_update.task_info['checkpoint_file']
            new_task = wfi.restart_task(task, checkpoint_file)
            if new_task is None:
                log.info('No more restarts')
                archive_fail_workflow(db, state_update.wf_id)
                return True
            db.workflows.add_task(new_task.id, state_update.wf_id, new_task.name, "WAITING")
            # Submit the restart task
            tasks = [new_task]
            wf_utils.schedule_submit_tasks(state_update.wf_id, tasks)
            log.info(f'Task {state_update.task_id} restarted')
            return True
        return False

    def handle_state_change(self, state_update, task, wfi, db):
        """Handle a normal state change for a task."""
        if state_update.job_state == 'COMPLETED':
            for output in task.outputs:
                if output.glob is not None:
                    wfi.set_task_output(task, output.id, output.glob)
                else:
                    wfi.set_task_output(task, output.id, "temp")
            tasks = wfi.finalize_task(task)
            wf_state = wfi.get_workflow_state()
            if tasks and wf_state != 'PAUSED':
                wf_utils.schedule_submit_tasks(state_update.wf_id, tasks)

            if wfi.workflow_completed():
                wf_id = wfi.workflow_id
                log.info(f"Workflow {wf_id} Completed")
                archive_workflow(db, state_update.wf_id)
                log.info('Workflow Completed')

        # If the job failed and it doesn't include a checkpoint-restart hint,
        # then fail the entire workflow
        if state_update.job_state == 'FAILED':
            set_dependent_tasks_dep_fail(db, wfi, state_update.wf_id, task)
            log.info("Workflow failed")
            wf_id = wfi.workflow_id
            archive_fail_workflow(db, wf_id)

        if state_update.job_state == 'BUILD_FAIL':
            log.error(f'Workflow failed due to failed container build for task {task.name}')
            archive_fail_workflow(db, state_update.wf_id)

    def update_task_state(self, state_update, db):
        """Update the state of a single task from the task manager."""
        wfi = wf_utils.get_workflow_interface(state_update.wf_id)
        task = wfi.get_task_by_id(state_update.task_id)
        wfi.set_task_state(task, state_update.job_state)
        db.workflows.update_task_state(state_update.task_id, state_update.wf_id,
                                       state_update.job_state)

        self.handle_metadata(state_update, task, wfi)
        if not self.handle_checkpoint_restart(state_update, task, wfi, db):
            self.handle_state_change(state_update, task, wfi, db)
