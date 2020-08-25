"""MARS evaluation program.

Evaluate the performance of the MARS algorithm within BEE by
comparing it with other commonly used algorithms like Backfill,
FCFS and SJF.
"""

import argparse
import subprocess
import time
import requests
import json

# Used for plotting results
import numpy as np
import matplotlib.pyplot as plt


SCHED_PORT = '5100'


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
        time.sleep(6)

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
    parser.add_argument('--resource-file', dest='resource_file',
                        help='json resource file to use', required=True)
    args = parser.parse_args()

    # TODO: Set resources
    # resources = []
    with open(args.resource_file) as fp:
        resources = json.load(fp)
    tasks = read_logfile(args.logfile)

    # Run FCFS or Backfill
    # TODO: Record averaged result parameters
    results = {}
    for algorithm in ['sjf', 'fcfs', 'backfill', 'mars']:
        print('Testing', algorithm)
        time.sleep(1)
        data = []
        with Scheduler(algorithm=algorithm) as link:
            # TODO: Set the proper workflow name later
            workflow_name = 'test-workflow'
            res_link = f'{link}/resources'
            wfl_link = f'{link}/workflows/{workflow_name}/jobs'
            # Generate the resources
            requests.put(res_link, json=resources)

            # TODO: PUT Workflows for evaluation
            # Work with chunks of 512 tasks
            CHUNK_SIZE = 10
            for i in range(0, len(tasks), CHUNK_SIZE):
                j = len(tasks) - i
                j = j if j < CHUNK_SIZE else CHUNK_SIZE
                print('Sending tasks from', i, 'to', i + j)
                tasks_send = tasks[i:i + j]
                r = requests.put(wfl_link, json=tasks_send)
                data.append(r.json())
                # print(r.json())
        # Get scheduling results for comparison
        total_time = 0
        for group in data:
            try:
                start_time = min(task['allocations'][0]['start_time']
                                 for task in group if task['allocations'])
                end_time = max(task['allocations'][0]['start_time']
                               + task['requirements']['max_runtime']
                               for task in group if task['allocations'])
                total_time += end_time - start_time
            except ValueError:
                total_time += 0
        results[algorithm] = {
            # Average time taken for a set of tasks to run (averaged)
            'avg_time': float(total_time) / len(data)
        }
        # data = r.json()
        # print(data)
        # TODO
        # break

    # Setup and display the graph
    fig, ax = plt.subplots()
    labels = [algorithm for algorithm in results]
    x = np.arange(len(labels))
    y = [results[algorithm]['avg_time'] for algorithm in results]
    rects = ax.bar(x, y, 0.6, label='Average Times', bottom=(min(y) - 20))
    ax.set_title('Workflow Times for each algorithm ("%s", "%s")'
                 % (args.logfile, args.resource_file))
    ax.set_ylabel('Total workflow time (s)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)

    def autolabel(rects):
        """Add labels to each rectangle.

        Add labels to each rectangle.
        """
        for rect in rects:
            height = rect.get_height()
            ax.annotate('%i' % height,
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords='offset points', ha='center',
                        va='bottom')

    autolabel(rects)
    plt.show()

if __name__ == '__main__':
    main()
