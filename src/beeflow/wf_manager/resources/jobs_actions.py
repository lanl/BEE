# This class is where we act on existing jobs
class JobActions(Resource):
    """Class to handle job actions."""

    def __init__(self):
        """Initialize JobActions class with passed json object."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    @staticmethod
    @validate_wf_id
    def post(wf_id):
        """Start job. Send tasks to the task manager."""
        # Get dependent tasks that branch off of bee_init and send to the scheduler
        wfi.execute_workflow()
        tasks = wfi.get_ready_tasks()
        # Convert to a scheduler task object
        sched_tasks = tasks_to_sched(tasks)
        # Submit all dependent tasks to the scheduler
        allocation = submit_tasks_scheduler(sched_tasks)
        # Submit tasks to TM
        submit_tasks_tm(tasks)
        resp = make_response(jsonify(msg='Started workflow', status='ok'), 200)
        wf_id = wfi.workflow_id
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Running')
        return "Started Workflow"

    @staticmethod
    @validate_wf_id
    def get(wf_id):
        """Check the database for the current status of all the tasks."""
        (_, tasks) = wfi.get_workflow()
        task_status = ""
        for task in tasks:
            if task.name != "bee_init" and task.name != "bee_exit":
                task_status += f"{task.name}--{wfi.get_task_state(task)}\n"
        log.info("Returned query")
        resp = make_response(jsonify(msg=task_status, status='ok'), 200)
        return resp

    @staticmethod
    @validate_wf_id
    def delete(wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        resp = requests.delete(_resource('tm'))
        if resp.status_code != 200:
            log.info(f"Delete from task manager returned bad status: {resp.status_code}")
        wf_id = wfi.workflow_id
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Cancelled')

        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    @validate_wf_id
    def patch(self, wf_id):
        """Pause or resume workflow."""
        global WORKFLOW_PAUSED
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        if option == 'pause':
            WORKFLOW_PAUSED = True
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
            return resp
        if option == 'resume':
            if WORKFLOW_PAUSED:
                WORKFLOW_PAUSED = False
                resume()
            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        log.error("Invalid option")
        resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
        return resp

