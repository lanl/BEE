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
from psij import Job, JobExecutor, JobSpec, JobAttributes, ResourceSpec

from beeflow.common import log as bee_logging
from beeflow.common.worker.worker import (Worker, WorkerError)
from beeflow.common import validation

log = bee_logging.setup(__name__)


class PSIJWorker(Worker):
    """Main Psij worker class. """
    def __init__(self, default_account='', default_time_limit='', default_partition='', **kwargs):
        """ Construct the psij worker """
        super().__init__(**kwargs)
        self.ex = JobExecutor.get_instance("slurm")
        self.jobs = {}
        self.default_account = default_account
        self.default_time_limit = default_time_limit
        self.default_partition = default_partition
        
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

    def build_text(self, task):
        """Build text for the task script."""
        #Not needed for PSIJ
        pass

    def submit_task(self, task):
        #Get the requirements for the task
        nodes = task.get_requirement('beeflow:MPIRequirement', 'nodes', default=1)
        ntasks = task.get_requirement('beeflow:MPIRequirement', 'ntasks', default=1)
        partition = task.get_requirement('beeflow:SchedulerRequirement', 
                                         'partition',
                                         default=self.default_partition)
        time_limit = task.get_requirement('beeflow:SchedulerRequirement', 
                                        'timeLimit', 
                                        default=self.default_time_limit)
        time_limit = validation.time_limit(time_limit)
        account = task.get_requirement('beeflow:SchedulerRequirement', 'account',
                                       default=self.default_account)

        #Apply all of the information gathered to the job spec and submit
        js = JobSpec(executable='/bin/sh', arguments=task.command)
        job_attributes = JobAttributes(queue_name=partition,duration=time_limit,project_name=account)
        js.resource_spec = ResourceSpec(node_count=nodes, processes_per_node=(ntasks / nodes), process_count=ntasks)
        js.attributes = job_attributes
        job = Job(js)
        self.ex.submit(job)
        self.jobs[job.native_id] = job
        #TODO translate psi-j job status to beeflow job status
        beeflow_state = self.translate_state(job.status.state)
        return job.native_id,beeflow_state

    def cancel_task(self, job_id):
        self.jobs[job_id].cancel()
        job_state = "CANCELLED"
        return job_state

    def query_task(self, job_id):
        return self.translate_state(self.jobs[job_id].status.state)

