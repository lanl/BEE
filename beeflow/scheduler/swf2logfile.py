"""Convert an SWF file into a log file.

Convert an SWF file into a log file for training purposes.
"""
import sys

import beeflow.scheduler.mars as mars


TASK_SIZE = 256


# Note: This combines multiple submissions into one to make a workflow. Given
# that the original format wasn't in a workflow format, but more of a task
# format this may make unfair assumptions.
def workflow2vec(task, tasks):
    """Convert a workflow of tasks into a vector.

    Convert a workflow of tasks into a vector.
    """
    def task2vec(task):
        return [
            '0.0',  # TODO: Cost
            task[3],  # Runtime
        ]
    vec = task2vec(task)
    index = tasks.index(task)
    for i, t in enumerate(tasks):
        # Skip the task to be scheduled
        if i == index:
            continue
        vec.extend(task2vec(t))
    vlen = len(vec)
    if vlen < mars.VECTOR_SIZE:
        vec.extend(['0.0'] * (mars.VECTOR_SIZE - vlen))
    else:
        vec = vec[:mars.VECTOR_SIZE]
    return vec


def main():
    lines = [line for line in sys.stdin]
    length = len(lines)

    def split(lines):
        return [[i for i in line.split()] for line in lines]
    workflows = [split(line for line in lines[i:min(length, i + TASK_SIZE)]
                       if line[0] != ';')
                 for i in range(0, length, TASK_SIZE)]
    # Print each task submission for each workflow
    for workflow in workflows:
        for task in workflow:
            vec = workflow2vec(task, workflow)
            print(' '.join(vec))


if __name__ == '__main__':
    main()
