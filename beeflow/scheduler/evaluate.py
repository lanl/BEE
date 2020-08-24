"""MARS evaluation program.

Evaluate the performance of the MARS algorithm within BEE by
comparing it with other commonly used algorithms like Backfill
and FCFS
"""

import argparse
import subprocess
import time
import requests


SCHED_PORT = '5100'


def launch_scheduler():
    """Launch the scheduler.
    """
    # TODO
    proc = subprocess.Popen([
        'python', 'beeflow/scheduler/scheduler.py',
        '-p', SCHED_PORT,
        '--no-config',
        '--use-mars',
    ])
    time.sleep(2)
    try:
        yield 'http://localhost:%s/bee_sched/v1' % SCHED_PORT
    finally:
        # Teardown
        proc.terminate()


class Scheduler:
    """Scheduler process class.

    Scheduler process class.
    """

    def __init__(self, algorithm):
        """Scheduler process class constructor.

        Scheduler process class constructor.
        """
        self.proc = subprocess.Popen([
            'python', 'beeflow/scheduler/scheduler.py',
            '-p', SCHED_PORT,
            '--no-config',
            # '--use-mars',
            '--algorithm', algorithm,  # Set the specific algorithm to use
        ])
        time.sleep(2)

    def __enter__(self):
        """Enter the runtime context.

        Enter the runtime context.
        :rtype: str, the link to use to connect to the scheduler
        """
        return 'http://localhost:%s/bee_sched/v1' % SCHED_PORT

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context.

        Exit the runtime context.
        """
        self.proc.terminate()


def read_logfile(logfile):
    """Read a workflow from a logfile.

    Read a workflow from a logfile.
    :param logfile: name of the logfile to read
    :type logfile: str
    :rtype: dict, set of tasks to pass to the scheduler REST api
    """
    # TODO: Determine logfile type (swf), read it and convert it into a set of
    tasks = []
    with open(logfile) as fp:
        for line in fp:
            split = line.split()
            # Skip comments
            if split[0] == ';':
                continue
            print(line)
            print(split)
            # submit_time = int(split[1])
            # wait_time = int(split[2])
            task_id = int(split[0])
            runtime = int(split[3])
            used_memory = int(split[6])
            procs = int(split[4])
            req_mem = int(split[9])
            # print(runtime, used_memory, procs, req_mem)
            # TODO
            tasks.append({
                'workflow_name': logfile,
                'task_name': task_id,
                'requirements': {
                    'max_runtime': runtime,
                    'cores': procs,
                }
            })
    # tasks
    return tasks


def main():
    parser = argparse.ArgumentParser(description='MARS evaluation program')
    # TODO: Parse proper arguments
    parser.add_argument('--logfile', dest='logfile',
                        help='name of logfile to use for evaluation',
                        required=True)
    args = parser.parse_args()

    # TODO: Set resources
    resources = []
    tasks = read_logfile(args.logfile)
    print(tasks)

    # Run FCFS or Backfill
    for algorithm in ['sjf', 'fcfs', 'backfill', 'mars']:
        with Scheduler(algorithm=algorithm) as link:
            # TODO: Set the proper workflow name later
            workflow_name = 'test-workflow'
            res_link = f'{link}/resources'
            wfl_link = f'{link}/workflows/{workflow_name}/jobs'
            print(res_link)
            print(wfl_link)
            # Generate the resources
            max_cores = max([task['requirements']['cores'] for task in tasks])
            resources = [
                {
                    'id_': 'resource-0',
                    'cores': max_cores,
                }
            ]
            requests.put(res_link, json=resources)

            # TODO: PUT Workflows for evaluation
            # Work with chunks of 512 tasks
            CHUNK_SIZE = 512
            for i in range(0, len(tasks), CHUNK_SIZE):
                j = len(tasks) - i
                j = j if j < CHUNK_SIZE else CHUNK_SIZE
                print('Sending tasks from', i, 'to', i + j)
                tasks_send = tasks[i:i + j]
                r = requests.put(wfl_link, json=tasks_send)
                print(r.json())
            # data = r.json()
            # print(data)
        # TODO
        break

    # Run MARS
    # with Scheduler(algorithm='mars') as link:
    #     # TODO
    #     pass

if __name__ == '__main__':
    main()
