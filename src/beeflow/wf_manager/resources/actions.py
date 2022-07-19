from flask_restful import Resource

def tasks_to_sched(tasks):
    """Convert gdb tasks to sched tasks."""
    sched_tasks = []
    for task in tasks:
        sched_task = {
            'workflow_name': 'workflow',
            'task_name': task.name,
            'requirements': {
                'max_runtime': 1,
                'nodes': 1
            }
        }
        sched_tasks.append(sched_task)
    return sched_tasks


# Submit a list of tasks to the Scheduler
def submit_tasks_scheduler(tasks):
    """Submit a list of tasks to the scheduler."""
    sched_tasks = tasks_to_sched(tasks)
    # The workflow name will eventually be added to the wfi workflow object
    try:
        resp = requests.put(_resource('sched', "workflows/workflow/jobs"), json=sched_tasks)
    except requests.exceptions.ConnectionError:
        log.error('Unable to connect to scheduler to submit tasks.')
        return

    if resp.status_code != 200:
        log.info(f"Something bad happened {resp.status_code}")
    return resp.json()


# This class is where we act on existing jobs
class JobActions(Resource):
    """Class to handle job actions."""

    def __init__(self):
        """Initialize JobActions class with passed json object."""
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('option', type=str, location='json')

    @staticmethod
    def post(wf_id):
        """Start workflow. Send ready tasks to the task manager."""
        #--CheckWorkflowState
        state = wfi.get_workflow_state()
        if state == 'RUNNING' or state == 'PAUSED' or state == 'COMPLETED':
            resp = make_response(jsonify(msg='Cannot start workflow it is currently'
                                        f'{state.capitalize()}.', 
                                            status='ok'), 200)
            return resp
        wfi.execute_workflow()
        tasks = wfi.get_ready_tasks()
        # Convert to a scheduler task object
        #--ConvertTasksToSchedFormat
        sched_tasks = tasks_to_sched(tasks)
        # Submit all dependent tasks to the scheduler
        #--SubmitTasksToScheduler
        allocation = submit_tasks_scheduler(sched_tasks)  # NOQA

        # Submit tasks to TM
        #--SubmitTasksToTaskManager
        submit_tasks_tm(tasks)
        #--CreateWorkflowStatusFile
        wf_id = wfi.workflow_id
        workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
        status_path = os.path.join(workflow_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Running')
        resp = make_response(jsonify(msg='Started workflow!', status='ok'), 200)
        return resp

    @staticmethod
    def get(wf_id):
        """Check the database for the current status of all tasks."""
        if wfi is not None:
            (_, tasks) = wfi.get_workflow()
            tasks_status = ""
            for task in tasks:
                tasks_status += f"{task.name}--{wfi.get_task_state(task)}"
                if task != tasks[len(tasks) - 1]:
                    tasks_status += '\n'
            log.info("Returned query")
            workflow_dir = os.path.join(bee_workdir, 'workflows', wf_id)
            status_path = os.path.join(workflow_dir, 'bee_wf_status')
            with open(status_path, 'r') as status:
                wf_status = status.readline()
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='ok'), 200)
        else:
            log.info(f"Bad query for wf {wf_id}.")
            wf_status = 'No workflow with that ID is currently loaded'
            tasks_status = 'Unavailable'
            resp = make_response(jsonify(tasks_status=tasks_status,
                                 wf_status=wf_status, status='not found'), 404)
        return resp

    @staticmethod
    def delete(wf_id):
        """Send a request to the task manager to cancel any ongoing tasks."""
        try:
            resp = requests.delete(_resource('tm'))
        except requests.exceptions.ConnectionError:
            log.error('Unable to connect to task manager to delete.')
            resp = make_response(jsonify(status='Could not cancel'), 404)
            return
        if resp.status_code != 200:
            log.info(f"Delete from task manager returned bad status: {resp.status_code}")
        workflows_dir = os.path.join(bee_workdir, 'workflows')
        status_path = os.path.join(workflows_dir, 'bee_wf_status')
        with open(status_path, 'w') as status:
            status.write('Cancelled')

        # Remove all tasks currently in the database
        if wfi.workflow_loaded():
            wfi.finalize_workflow()
        log.info("Workflow cancelled")
        resp = make_response(jsonify(status='cancelled'), 202)
        return resp

    def patch(self, wf_id):
        """Pause or resume workflow."""
        # Stop sending jobs to the task manager
        data = self.reqparse.parse_args()
        option = data['option']
        workflow_state = wfi.get_workflow_state()
        if workflow_state == 'PAUSED' and option == 'pause':
            resp_msg = 'Workflow already paused'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'RUNNING' and option == 'resume':
            resp_msg = 'Workflow already running'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'SUBMITTED':
            if option == 'pause':
                resp_msg = 'Workflow has not been started yet. Cannot Pause.'
            elif option == 'resume':
                resp_msg = 'Workflow has not been started yet. Cannot Resume.'
            log.info(resp_msg)
            resp = make_response(jsonify(status=resp_msg), 200)
            return resp
        elif workflow_state == 'COMPLETED':
            log.info('Workflow Completed. Cannot Pause.')
            resp = make_response(jsonify(status='Can only pause running workflows'), 200)
            return resp

        if option == 'pause':
            wfi.pause_workflow()
            log.info("Workflow Paused")
            resp = make_response(jsonify(status='Workflow Paused'), 200)
        elif option == 'resume':
            wfi.resume_workflow()
            tasks = wfi.get_ready_tasks()
            sched_tasks = tasks_to_sched(tasks)
            submit_tasks_scheduler(sched_tasks)
            submit_tasks_tm(tasks)

            log.info("Workflow Resumed")
            resp = make_response(jsonify(status='Workflow Resumed'), 200)
            return resp
        else:
            resp = make_response(jsonify(status='Pause/Resume recieved invalid option'), 200)
            log.error("Invalid option")
            resp = make_response(jsonify(status='Invalid option for pause/resume'), 400)
            return resp
