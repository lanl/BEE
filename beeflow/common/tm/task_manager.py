"""Task Manager submits & manages tasks and communicates with Work Flow Manager.

Submits and manages tasks & communicates status to the Work Flow Manager, through RESTful API.
For now submit jobs serially.
"""
import time
import os
import json

from beeflow.common.data.wf_data import Task
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker


def main():
    """Mock Task Manager populates a Task dictionary to use to submit tasks."""
    worker = WorkerInterface(SlurmWorker)

    def submit_task(task):
        return worker.submit_task(task)

    # no restful api now, so read Tasks from json file, note the file will be 
    # deleted and new tasks can be read from writing a new file 

    # no restful api now, so populate Task manually using by_hand example from Al
    ready_tasks = []
    
    # t_input = 'grep.in'
    # t_output = 'grep.out'
    # grep_string = 'database'
    # tasks.append(
    #     Task('GREP', command=['grep', '-i', grep_string, t_input, '>', t_output],
    #          hints=None, subworkflow=None, inputs={t_input}, outputs={t_output}))

    # t_input = 'grep.out'
    # t_output = 'wc.out'

    # Will eventually be a server that uses RESTful API's
    # for now continuously loop 
    # read the task file if any new tasks exist add them to the queue
    # 
    # This will be replaced by retrieving any messages for the RESTful interface
    # Jobs will be submitted as soon as a task is recieved
    # For now assuming only getting job submissions from the Work Flow Manager

    while True:
        # For now put json file in tasks.json, you may add a task one at a time 
        if os.path.exists('sent_task.json'):
            f = open('sent_task.json')
            with open('sent_task.json') as f:
                sent_task = json.load(f)
                os.remove('sent_task.json')
                task_cmd = sent_task['command'].split(',')
                print(sent_task['outputs'])
                print(sent_task)
                # submit job TODO actually use hints and subworkflow
                task = Task(name=sent_task['name'], 
                            command=task_cmd, 
                            hints=None, 
                            subworkflow=None, 
                            inputs=sent_task['inputs'], 
                            outputs=sent_task['outputs'])
            ready_tasks.append(task)
        if ready_tasks: 
            task = ready_tasks.pop(0)
            job_info = submit_task(task)
            job_state = job_info[1]
            job_id = job_info[0]
            print('Task: ', task.name, '  Job: ', job_id, 'submitted, ', job_state)

            while job_state != 'COMPLETED':
            # check for state change every 5 seconds FIX THIS
                time.sleep(5)
                job_info = worker.query_job(job_id)
                if job_info[1] != job_state:
                    job_state = job_info[1]
                    print('   ', job_id, 'changed state: ', job_state)

main()
