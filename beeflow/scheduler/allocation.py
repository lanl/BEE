"""Allocation code for storing task and workflow resource information.

Code for holding allocation details for various tasks/jobs and
workflows (such as number of nodes, partitions, and other more
specific resource details).
"""

import beeflow.scheduler.sched_types as sched_types


def schedule_all(algorithm, tasks, resources):
    """Schedule a list of independent tasks.

    Schedule a list of independent tasks on given resources, using
    the specified algorithm.
    :param algorithm: algorithm class to use
    :type algorithm: algorithm class (not an instance)
    :param tasks: tasks to schedule
    :type tasks: list of instance of Task
    :param resources: available resources
    :type resources: list of instance of Resource
    """
    algorithm.schedule_all(tasks, resources)
