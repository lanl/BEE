from time import sleep
from beeflow.common.worker.worker_interface import WorkerInterface

Worker = WorkerInterface() #instatiate class

script = 'bad.slr'

SCRIPTS = ['good.slr', 'bad.slr']
for job_script in SCRIPTS:

    print("Submitting ", job_script)
    job_info = Worker.submit_job(job_script)
    if job_info[0] == 1:
        print('Failed with the following error:')
        print(job_info[1], '\n')
        if 'error' in job_info[1]:
            print ('found error')
    else:
        print('Successful: job_id = ', job_info[0],
              ' job_state = ', job_info[1], '\n')
        job_id_good = job_info[0]

job_state = ''
print('Querying ', job_id_good)
job_info = Worker.query_job(job_id_good)
print(job_info)

print(job_state)
print('Attempting to kill job ', job_id_good)
job_info = Worker.cancel_job(job_id_good)

print('Querying ', job_id_good)
job_info = Worker.query_job(job_id_good)
job_state = job_info[1]
print(job_state)


