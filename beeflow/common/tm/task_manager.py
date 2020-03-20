"""Task Manager submits & manages tasks and communicates with Work Flow Manager.

Submits and manages tasks.
Communicates status to the Work Flow Manager, through RESTful API.
"""
import time
import os
import json

from beeflow.common.data.wf_data import Task
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker


def main():
    """Task Manager build and submits tasks, from json file."""
    worker = WorkerInterface(SlurmWorker)

    def submit_task(task):
        """Submit task - write script and sumbit job."""
        return worker.submit_task(task)

    def read_task(json_file):
        """Get task from json file, will come from WFM."""
        with open(json_file) as json_f:
            sent_task = json.load(json_f)
            os.remove('sent_task.json')
            task_cmd = sent_task['command'].split(',')
            # fix TODO submit does not use hints and subworkflow
            # fix TODO task_id should be part of task
            task = Task(name=sent_task['name'],
                        command=task_cmd,
                        hints=None,
                        subworkflow=None,
                        inputs=sent_task['inputs'],
                        outputs=sent_task['outputs'])
            task_id = sent_task['task_id']
            return task, task_id

    def update_job_queue(job_queue):
        """Check and update states of jobs in queue, remove completed jobs."""
        for job in job_queue:
            task_id = list(job)[0]
            current_task = job[task_id]
            job_id = current_task['job_id']
            state = worker.query_job(job_id)
            # fix TODO what to do if query is not good for now it will just keep trying
            if state[0] == 1:
                job_state = state[1]
            if job_state != current_task['job_state']:
                current_task['job_state'] = job_state
                # Send new state to WFM here
                print('Task changed state:', task_id, current_task['name'], job_id, job_state)
            # Remove completed job from queue
            # fix TODO needs to be an abstract state
            if job_state in ('COMPLETED', 'CANCELLED'):
                # fix TODO Send job info to WFM
                print('Job done:', task_id, current_task['name'], job_id, job_state)
                job_queue.remove(job)

    # fix TODO work with REST interface
    # no restful api now, so read Tasks from json file

    submit_queue = []  # tasks ready to be submitted
    job_queue = []  # jobs that are being monitored

    # fix TODO Will eventually be a server that uses RESTful API's
    # for now: a timed loop
    timer = 120
    start = time.time()
    while True:
        # read tasks from file and add to queue to submit
        if os.path.exists('sent_task.json'):
            task, task_id = read_task('sent_task.json')
            submit_queue.append({task_id: task})

        # submit tasks received
        while len(submit_queue) >= 1:
            task_dict = submit_queue.pop(0)
            task_id = list(task_dict)[0]
            task = task_dict.get(task_id)
            job_id, job_state = submit_task(task)
            # fix TODO prints will become message sends to WFM
            if job_id == -1:
                # send task failed message to WFM
                print('Task submission failed:', task_id, task.name, job_state)
            else:
                # place job in queue to monitor and send intial state to WFM
                job_queue.append({task_id: {'name': task.name, 'job_id': job_id,
                                            'job_state': job_state}})
                print('Submitted: ', task_id, task.name, 'Job:', job_id, job_state)

        # Check state of jobs in queue, update states and send updates to WFM
        update_job_queue(job_queue)
        time.sleep(5)
        # The following is temporary just to insure task manager stops
        if time.time() > start + timer:
            if len(job_queue) == 0 & len(submit_queue) == 0:
                print('Task Manager Shut Down')
                break
            print('Task Manager time is up but there are still queued tasks.')
            time.sleep(10)


main()
