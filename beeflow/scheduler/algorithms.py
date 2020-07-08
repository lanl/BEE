"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import random
import time

# import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types
import beeflow.scheduler.util as util


class Algorithm(abc.ABC):
    """Scheduling algorithm abstract class.

    Base abstract class for implementing a scheduling algorithm.
    """

    @staticmethod
    @abc.abstractmethod
    def schedule_all(tasks, resources):
        """Schedule all tasks with the implemented algorithm.

        Schedule all tasks with the implemented algorithm.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """


class FCFS(Algorithm):
    """FCFS scheduling algorithm.

    This class holds the scheduling code used for the FCFS
    scheduling algorithm.
    """

    @staticmethod
    def schedule_all(tasks, resources):
        """Schedule a list of independent tasks with FCFS.

        Schedule an entire list of tasks using FCFS. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        # TODO: Move code that deals directly with requirements other
        # than 'max_runtime' into the Resource and Allocation classes.
        allocations = []
        # Continue while there are still tasks to schedule
        for task in tasks:
            for resource in resources:
                if resource.runs(task):
                    allocated = [a for a in allocations
                                 if a.id_ == resource.id_]
                    # allocation = resource.allocate(task, allocated)
                    start_time = int(time.time())
                    # Determine totals
                    cores = (task.requirements['cores']
                             if 'cores' in task.requirements else 1)
                    # Determine the possible start_time
                    if ((resource.cores - sum(a.cores for a in allocated))
                            < cores):
                        # Note: this leaves some "open" space since there
                        # is a possibility that the task could fit into
                        # a time slot before the longest already scheduled
                        # task has filled in that area
                        #
                        # TODO: What is the default max_runtime? - Is this
                        # set in bee.conf?
                        start_time += max(a.max_runtime for a in allocated)
                    alloc = sched_types.Allocation(
                        id_=resource.id_, cores=cores, start_time=start_time,
                        max_runtime=task.requirements['max_runtime'])
                    allocations.append(alloc)
                    # TODO: Handle multiple resource allocations for a task
                    task.allocations = [alloc]
                    break


class Backfill(Algorithm):
    """Backfill scheduling algorithm.

    This class holds the scheduling code used for the Backfill
    scheduling algorithm.
    """

    @staticmethod
    def schedule_all(tasks, resources):
        """Schedule a list of independent tasks with Backfill.

        Schedule an entire list of tasks using Backfill. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        # TODO: This time may be invalidated if the algorithm
        # takes too long
        tasks = tasks[:]
        current_time = int(time.time())
        allocations = []
        while tasks:
            # Get a task to schedule
            task = tasks.pop(0)
            total = util.calculate_remaining(resources, [])
            if not total.runs(task):
                continue
            # Can this task run immediately?
            start_time = current_time
            max_runtime = task.requirements['max_runtime']
            overlap = util.calculate_overlap(allocations, start_time,
                                             max_runtime)
            remaining = util.calculate_remaining(resources, overlap)
            if remaining.runs(task):
                allocs = util.allocate_aggregate(resources, overlap, task,
                                                 start_time)
                allocations.extend(allocs)
                task.allocations = allocs
                continue
            # This job must run later, so find the shadow time (the earliest
            # time at which the job can run)
            shadow_time = current_time
            times = [a.start_time + a.max_runtime for a in allocations]
            times.sort()
            for start_time in times:
                overlap = util.calculate_overlap(allocations, start_time,
                                                 max_runtime)
                remaining = util.calculate_remaining(resources, overlap)
                if remaining.runs(task):
                    shadow_time = start_time
                    allocs = util.allocate_aggregate(resources, allocations,
                                                     task, start_time)
                    allocations.extend(allocs)
                    task.allocations = allocs
            # Backfill tasks
            tasks_left = []
            for task in tasks:
                times = [current_time]
                times.extend(a.start_time + a.max_runtime for a in allocations)
                max_runtime = task.requirements['max_runtime']
                # Ensure that the task will finish before the shadow time
                times = [t for t in times if (t + max_runtime) <= shadow_time]
                times.sort()
                # Determine when it can run (if it can be backfilled)
                for start_time in times:
                    overlap = util.calculate_overlap(allocations, start_time,
                                                     max_runtime)
                    remaining = util.calculate_remaining(resources, overlap)
                    if remaining.runs(task):
                        allocs = util.allocate_aggregate(resources, overlap,
                                                         task, start_time)
                        allocations.extend(allocs)
                        task.allocations = allocs
                        break
                # Could not backfill this task
                if not task.allocations:
                    tasks_left.append(task)
            # Reset the tasks to the remaining list
            tasks = tasks_left


def choose():
    """Choose which algorithm to run at this point.

    Determine which algorithm class needs to run and return it.
    :rtype: class derived from Algorithm (not an instance)
    """
    # TODO: This decision should not be made randomly
    return FCFS if random.randint(0, 1) else Backfill
