"""Task Manager submits & manages tasks and communicates with Work Flow Manager.

Submits and manages tasks & communicates status to the Work Flow Manager, through RESTful API.
"""
import os
import string
import time

from flask import Flask 
from flask_restful import Resource, Api, reqprse, fields

from beeflow.common.wf_interface import WorkflowInterface
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker


wfi = WorkflowInterface()
worker = WorkerInterface(SlurmWorker)

# for now we will use this directory for task manager scripts and write them out
# we will have a debug or logging option 
job_template_file = os.path.expanduser('~/.beeflow/scripts/job.template')

# make directory if it does not exist (for now use date would like workflow name)
template_dir = os.path.dirname(job_template_file)
script_dir = template_dir + '/workflow-' + time.strftime("%Y%m%d-%H%M%S")
os.makedirs(script_dir, exist_ok=True)

# check for a template, if not make the script without it
job_template = ''

no_file_resp = {
    'msg':'No task file found',
    'status':'error'
}

def load_template():
    try:
        f = open(job_template_file, 'r')
        job_template = f.read()
    except OSError as err:
        print("OS error: {0}".format(err))
        print('No job_template: creating a simple job template!')
        job_template = '#! /bin/bash\n#SBATCH\n'


class TaskSubmit(Resource):
    def __init(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('task', type=FileStorage, location='tasks')
        super(TaskSubmit, self).__init__()
    
    # WFM sends a job to the task manager
    def post(self):
        data = self.reqparse.parse_args()
        task = data['task']

        # If there's no file 
        if task == "":
            return no_file_resp
        else:   
            filename = "task"
            task.save(os.path.join(flask_app.config['UPLOAD_FOLDER'], filename))


class TaskActions(Resource):
    def __init(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('workflow', type=FileStorage, location='tasks')

        # Query 
        def post(self):
            pass

        def 


# no restful api now, so populate Task and Requirment by hand from Al's stuff
tasks = []
task_input = 'grep.in'
task_output = 'grep.out'
grep_string = 'database'
tasks.append(wfi.add_task(
    'GREP', command=['grep', '-i', grep_string , task_input, '>', task_output],
    inputs={task_input}, outputs={task_output}))

task_input = 'grep.out'
task_output = 'wc.out'
tasks.append(wfi.add_task(
    'WC', command=['wc', '-l', task_input, '>', task_output],
    inputs={task_input}, outputs={task_output}))

# Will eventually be a server that uses RESTful API's
# for now  loop until tasks defined above are deleted
while tasks:
    task = tasks.pop(0)
    task_script_file = script_dir + '/' +  task.name + '-' + str(task.id) + '.sh'
    s = string.Template(job_template)
    # substitute template & add the command good for this simple command Needs Work
    task_script = s.substitute(task.__dict__) + ' '.join(task.command)

    try:
        f = open(task_script_file, 'w')
        f.write(task_script)
        f.close()
    except OSError as err:
        print("OS error: {0}".format(err))

    """Submit the job and query until state = 'COMPLETED'
       The following will continue until the job is completed.
       We would send these states to the Work Flow manager who should update the
       database. Also for now I'm assuming the job actually is submitted and all is       well. Need to put in place checks.
    """
    job_info = worker.submit_job(task_script_file)
    job_state = job_info[1]
    job_id = job_info[0]
    print('Task: ', task.name, '  Job: ', job_id, 'submitted, ', job_state)
    while (job_state != 'COMPLETED'):
        #check for state change every 5 seconds FIX THIS
        time.sleep(5)
        job_info = worker.query_job(job_id)
        if job_info[1] != job_state:
            job_state = job_info[1]
            print('   ', job_id, 'changed state: ', job_state)
       
        
