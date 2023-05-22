"""PSI-J worker for work load management.
https://exaworks.org/psij
Builds command for submitting jobs through psij.
"""

import subprocess
import json
import urllib
import getpass
import requests_unixsocket
import requests
import psij

from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)
from beeflow.common import validation

log = bee_logging.setup(__name__)


class PsijWorker(Worker):
    """Main Psij worker class. """
    def __init__(self, **kwargs):
        """ Construct the psij worker """
        super().__init__(**kwargs)
        self.ex = JobExecutor.get_instance("local")
        jobs = {}
        
    def write_script(self, task):
        """Build task script; returns filename of script."""
        task_text = self.build_text(task)
        task_script = f'{self.task_save_path(task)}/{task.name}-{task.id}.sh'
        with open(task_script, 'w', encoding='UTF-8') as script_f:
            script_f.write(task_text)
            script_f.close()
        return task_script

    def translate_state(self, job_state):
        state_table = {
                'ACTIVE': 'RUNNING',
                'CANCELED': 'CANCELLED',
                'COMPLETED': 'COMPLETED',
                'FAILED': 'FAILED',
                'NEW': 'PENDING',
                'QUEUED': 'PENDING',
                }

        return state_table[job_state]

    def submit_task(self, task):
        #Get the executable for the task

        script = self.build_text(task)
        script_path = os.path.join(self.task_save_path(task), f'{task.name}-{task.id}.sh')
        with open(script_path, 'w', encoding='UTF-8') as fp:
            fp.write(script)
        """
        with subprocess.Popen(['/bin/sh', script_path]) as taskid:
            self.tasks[task.id] = taskid
        return (task.id, 'PENDING')
        """

        #Get the requirements for the task
        nodes = task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=1)
        partition = task.get_requirement('beeflow:SchedulerRequirement',
        time_limit = task.get_requirement('beeflow:SchedulerRequirement', 'timeLimit',
                                          default=self.default_time_limit)
        time_limit = validation.time_limit(time_limit)
        account = task.get_requirement('beeflow:SchedulerRequirement', 'account',
                                       default=self.default_account)

        #Apply all of the information gathered to the job spec and submit
        js = JobSpec(executable='/bin/sh', arguments=[write_script(task)])
        job_attributes = JobAttributes(queue_name=partition,duration=time_limit,project_name=account)
        js.resource_spec = ResourceSpec(node_count=nodes, processes_per_node=(ntasks / nodes), process_count=ntasks)
        js.attributes = job_attributes
        job = Job(js)
        self.ex.submit(job)
        self.jobs[job.native_id] = job
        #TODO translate psi-j job status to beeflow job status
        beeflow_state = translate_state(job.status.state)
        return job.native_id,beeflow_state

    def cancel_task(self, job_id):
        self.jobs[job_id].cancel()
        job_state = "CANCELLED"
        return job_state

    def query_task(self, job_id):
        return translate_state(self.jobs[job_id].status.state)

