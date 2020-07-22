"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import random
import time

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
        allocations = []
        start_time = int(time.time())
        # Continue while there are still tasks to schedule
        for task in tasks:
            # Check if the task can run at all
            remaining = sched_types.rsum(*resources)
            if not remaining.fits_requirements(task.requirements):
                # Can't run this task at all
                continue
            max_runtime = task.requirements.max_runtime
            while True:
                overlap = util.calculate_overlap(allocations, start_time,
                                                 max_runtime)
                remaining = sched_types.diff(sched_types.rsum(*resources),
                                             sched_types.rsum(*overlap))
                if remaining.fits_requirements(task.requirements):
                    allocs = util.allocate_aggregate(resources, overlap, task,
                                                     start_time)
                    allocations.extend(allocs)
                    task.allocations = allocs
                    break
                # Set the next time increment to check
                start_time = min(a.start_time + a.max_runtime
                                 for a in overlap)


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
            total = sched_types.rsum(*resources)
            if not total.fits_requirements(task.requirements):
                continue
            # Can this task run immediately?
            start_time = current_time
            max_runtime = task.requirements.max_runtime
            overlap = util.calculate_overlap(allocations, start_time,
                                             max_runtime)
            remaining = util.calculate_remaining(resources, overlap)
            if remaining.fits_requirements(task.requirements):
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
                if remaining.fits_requirements(task.requirements):
                    shadow_time = start_time
                    allocs = util.allocate_aggregate(resources, overlap, task,
                                                     start_time)
                    allocations.extend(allocs)
                    task.allocations = allocs
                    break
            # Backfill tasks
            tasks_left = []
            for task in tasks:
                times = [current_time]
                times.extend(a.start_time + a.max_runtime for a in allocations)
                max_runtime = task.requirements.max_runtime
                # Ensure that the task will finish before the shadow time
                times = [t for t in times if (t + max_runtime) <= shadow_time]
                times.sort()
                # Determine when it can run (if it can be backfilled)
                for start_time in times:
                    overlap = util.calculate_overlap(allocations, start_time,
                                                     max_runtime)
                    remaining = util.calculate_remaining(resources, overlap)
                    if remaining.fits_requirements(task.requirements):
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


class MARS(Algorithm):
    """MARS Scheduler.

    MARS Scheduler.
    """

    def make_available_list(task, resources, allocations):
        """Make a list of available allocations for a task.

        Make a list of allocations for the given task that
        are in the near future.
        :param task: the task
        :type task: instance of Task
        :param resources: list of available resources
        :type resources: list of instance of Resource
        :param allocations: current allocations
        :type allocations: list of instance of Allocation
        """
        # TODO

    @staticmethod
    def schedule_all(tasks, resources):
        """Schedule a list of tasks on the given resources.

        Schedule a full list of tasks on the given resources
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of Resource
        """
        # TODO: Implement model loading function
        model = load_model()
        allocations = []
        for task in tasks:
            # Create a list of reasonable available time slots that can be
            # used by the model
            available = make_available_list(task, resources, allocations)
            # Choose the best allocation based on the model
            allocs = model.choose(task, available)
            allocations.extend(allocs)
            task.allocations = allocs


# TODO: Perhaps this value should be a config value
MEDIAN = 4

def choose(tasks):
    """Choose which algorithm to run at this point.

    Determine which algorithm class needs to run and return it.
    :param tasks: list of tasks:
    :type tasks: list of instance of Task
    :rtype: class derived from Algorithm (not an instance)
    """
    # TODO: Correctly choose based on size of the workflow
    return Backfill
    # return Backfill if len(tasks) < MEDIAN else RL
