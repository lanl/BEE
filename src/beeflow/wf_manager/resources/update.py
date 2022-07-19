from beeflow.wf_manager.common.defs import *

class JobUpdate(Resource):
    """Class to interact with an existing job."""

    def put(self):
        """Update the state of a task from the task manager."""
        #--ParseArguments
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task_id', type=str, location='form',
                                   required=True)
        self.reqparse.add_argument('job_state', type=str, location='form',
                                   required=True)
        self.reqparse.add_argument('metadata', type=str, location='form',
                                   required=False)
        self.reqparse.add_argument('output', location='form', required=False)

        global reexecute
        data = self.reqparse.parse_args()
        task_id = data['task_id']
        job_state = data['job_state']
        task = wfi.get_task_by_id(task_id)
        wfi.set_task_state(task, job_state)
        wf_profiler.add_state_change(task, job_state)

        if 'metadata' in data:
            if data['metadata'] is not None:
                metadata = jsonpickle.decode(data['metadata'])
                wfi.set_task_metadata(task, metadata)

        # Get output from the task
        if 'output' in data and data['output'] is not None:
            fname = f'{wfi.workflow_id}_{task.id}_{int(time.time())}.json'
            task_output_path = os.path.join(bee_workdir, fname)
            with open(task_output_path, 'w') as fp:
                json.dump(json.loads(data['output']), fp, indent=4)

        if job_state == "COMPLETED" or job_state == "FAILED":
            for output in task.outputs:
                if output.glob is not None:
                    wfi.set_task_output(task, output.id, output.glob)
                else:
                    wfi.set_task_output(task, output.id, "temp")
            tasks = wfi.finalize_task(task)
            state = wfi.get_workflow_state()
            if tasks and state != 'PAUSED':
                sched_tasks = tasks_to_sched(tasks)
                submit_tasks_scheduler(sched_tasks)
                submit_tasks_tm(tasks)


            if wfi.workflow_completed():
                log.info("Workflow Completed")

                # Save the profile
                wf_profiler.save()

                if archive and not reexecute:
                    gdb_workdir = os.path.join(bee_workdir, 'current_gdb')
                    wf_id = wfi.workflow_id
                    workflows_dir = os.path.join(bee_workdir, 'workflows')
                    workflow_dir = os.path.join(workflows_dir, wf_id)
                    # Archive GDB
                    shutil.copytree(gdb_workdir, workflow_dir + '/gdb')
                    # Archive Config
                    shutil.copyfile(os.path.expanduser("~") + '/.config/beeflow/bee.conf',
                                    workflow_dir + '/' + 'bee.conf')
                    status_path = os.path.join(workflow_dir, 'bee_wf_status')
                    with open(status_path, 'w') as status:
                        status.write('Archived')
                    archive_dir = os.path.join(bee_workdir, 'archives')
                    os.makedirs(archive_dir, exist_ok=True)
                    # archive_path = os.path.join(archive_dir, wf_id + '_archive.tgz')
                    archive_path = f'../archives/{wf_id}.tgz'
                    # We use tar directly since tarfile is apparently very slow
                    subprocess.call(['tar', '-czf', archive_path, wf_id], cwd=workflows_dir)
                else:
                    reexecute = False

                #else:

        resp = make_response(jsonify(status=f'Task {task_id} set to {job_state}'), 200)
        return resp

