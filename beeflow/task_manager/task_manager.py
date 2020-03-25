"""Task Manager submits & manages tasks and communicates with Work Flow Manager.

Submits and manages tasks & communicates status to the Work Flow Manager, through RESTful API.
For now submit jobs serially.
"""
import time

from flask import Flask
from flask_restful import Resource, Api, reqprse, fields

from beeflow.common.data.wf_data import Task
from beeflow.common.worker.worker_interface import WorkerInterface
from beeflow.common.worker.slurm_worker import SlurmWorker

flask_app = Flask(__name__)
api = Api(flask_app)

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


def main():
    """Mock Task Manager populates a Task dictionary to use to submit tasks."""
    worker = WorkerInterface(SlurmWorker)

    # no restful api now, so populate Task manually using by_hand example from Al
    tasks = []
    t_input = 'grep.in'
    t_output = 'grep.out'
    grep_string = 'database'
    tasks.append(
        Task('GREP', command=['grep', '-i', grep_string, t_input, '>', t_output],
             hints=None, subworkflow=None, inputs={t_input}, outputs={t_output}))

    t_input = 'grep.out'
    t_output = 'wc.out'
    tasks.append(
        Task('WC', command=['wc', '-l', t_input, '>', t_output],
             hints=None, subworkflow=None, inputs={t_input}, outputs={t_output}))

    # Will eventually be a server that uses RESTful API's
    # for now  loop until tasks defined above are deleted
    # This will be replaced by a queue of tasks associated with jobs
    # so that we can run them in parallel.
    print('')
    while tasks:
        task = tasks.pop(0)
        job_info = worker.submit_task(task)
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
