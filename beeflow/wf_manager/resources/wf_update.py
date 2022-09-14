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
from beeflow.cli import log


def archive_workflow(wf_id):
    """Archive a workflow after completion."""
    bee_workdir = wf_utils.get_bee_workdir()
    gdb_workdir = os.path.join(bee_workdir, 'current_run')
    workflows_dir = os.path.join(bee_workdir, 'workflows')
    workflow_dir = os.path.join(workflows_dir, wf_id)

    # Archive GDB
    shutil.copytree(gdb_workdir, workflow_dir + '/gdb')
    # Archive Config
    shutil.copyfile(os.path.expanduser("~") + '/.config/beeflow/bee.conf',
                    workflow_dir + '/' + 'bee.conf')

    wf_utils.update_wf_status(wf_id, 'Archived')

    archive_dir = os.path.join(bee_workdir, 'archives')
    os.makedirs(archive_dir, exist_ok=True)
    # archive_path = os.path.join(archive_dir, wf_id + '_archive.tgz')
    archive_path = f'../archives/{wf_id}.tgz'
    # We use tar directly since tarfile is apparently very slow
    subprocess.call(['tar', '-czf', archive_path, wf_id], cwd=workflows_dir)


class WFUpdate(Resource):
    """Class to interact with an existing workflow."""

    def __init__(self):
        """Set up arguments."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task_id', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='json',
                                   required=True)
        self.reqparse.add_argument('metadata', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('task_info', type=str, location='json',
                                   required=False)
        self.reqparse.add_argument('output', location='json', required=False)

    def put(self):
        """Update the state of a task from the task manager."""
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']

        wfi = wf_utils.get_workflow_interface()
        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)
        # wf_profiler.add_state_change(task, job_state)

        # Get metadata from update if available
        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                wfi.set_task_metadata(task, metadata)

        bee_workdir = wf_utils.get_bee_workdir()
        # Get output from the task
        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                old_metadata = wfi.get_task_metadata(task)
                old_metadata.update(metadata)
                wfi.set_task_metadata(task, old_metadata)

        if 'output' in data and data['output'] is not None:
            fname = f'{wfi.workflow_id}_{task.id}_{int(time.time())}.json'
            task_output_path = os.path.join(bee_workdir, fname)
            with open(task_output_path, 'w', encoding='utf8') as fp:
                json.dump(json.loads(data['output']), fp, indent=4)

        if job_state in ('COMPLETED', 'FAILED'):
            for output in task.outputs:
                if output.glob is not None:
                    wfi.set_task_output(task, output.id, output.glob)
                else:
                    wfi.set_task_output(task, output.id, "temp")
            tasks = wfi.finalize_task(task)
            state = wfi.get_workflow_state()
            if tasks and state != 'PAUSED':
                allocation = wf_utils.submit_tasks_scheduler(log, tasks)
                wf_utils.submit_tasks_tm(log, tasks, allocation)

            if wfi.workflow_completed():
                log.info("Workflow Completed")
                # Save the profile
                # wf_profiler.save()
                wf_id = wfi.workflow_id
                archive_workflow(wf_id)

        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp
