"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import os
import time

from beeflow.scheduler import resource_allocation


class Algorithm(abc.ABC):
    """Scheduling algorithm abstract class.

    Base abstract class for implementing a scheduling algorithm.
    """

    @staticmethod
    @abc.abstractmethod
    def load(**kwargs):
        """Load configuration for the algorithm."""

    @staticmethod
    @abc.abstractmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule all tasks with the implemented algorithm.

        Schedule all tasks with the implemented algorithm.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of resource_allocation.Resource
        """


class SJF(Algorithm):
    """Shortest job first algorithm.

    Class holding scheduling code for runing the shortest job first algorithm.
    """

    @staticmethod
    def load(**kwargs):
        """Load algorithm configuration, if necessary."""

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with SJF.

        Schedule a list of independent tasks with SFJ.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources list of instance of resource_allocation.Resource
        """
        # First sort the tasks by how long they are, then send them off to
        # FCFS
        tasks = tasks[:]
        tasks.sort(key=lambda task: task.requirements.max_runtime)
        FCFS.schedule_all(tasks, resources, **kwargs)


class FCFS(Algorithm):
    """FCFS scheduling algorithm."""

    @staticmethod
    def load(**kwargs):
        """Load algorithm configuration, if necessary."""

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with FCFS.

        Schedule an entire list of tasks using FCFS. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of resource_allocation.Resource
        """
        allocator = resource_allocation.TaskAllocator(resources)
        start_time = 0
        for task in tasks:
            if not allocator.fits_requirements(task.requirements):
                continue
            # Find the start_time
            while not allocator.can_run_now(task.requirements, start_time):
                start_time = allocator.get_next_end_time(start_time)
            task.allocations = allocator.allocate(task.requirements,
                                                  start_time)


class Backfill(Algorithm):
    """Backfill scheduling algorithm.

    This class holds the scheduling code used for the Backfill
    scheduling algorithm.
    """

    @staticmethod
    def load(**kwargs):
        """Load algorithm configuration, if necessary."""

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with Backfill.

        Schedule an entire list of tasks using Backfill. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of resource_allocation.Resource
        """
        tasks = tasks[:]
        current_time = 0
        allocator = resource_allocation.TaskAllocator(resources)
        while tasks:
            task = tasks.pop(0)
            # Can this task run at all?
            if not allocator.fits_requirements(task.requirements):
                continue
            # Can this task run immediately?
            start_time = current_time
            # max_runtime = task.requirements.max_runtime
            if allocator.can_run_now(task.requirements, start_time):
                allocs = allocator.allocate(task.requirements, start_time)
                task.allocations = allocs
                continue
            # This job must run later, so we need to find the shadow time
            # (earliest time at which the job can run)
            times = allocator.get_end_times()
            times.sort()
            shadow_time = 0
            for shadow_time in times:
                if allocator.can_run_now(task.requirements, shadow_time):
                    allocs = allocator.allocate(task.requirements, shadow_time)
                    task.allocations = allocs
                    break
            # Now backfill other tasks
            times.insert(0, current_time)
            remaining = []
            for backfill_task in tasks:
                max_runtime = backfill_task.requirements.max_runtime
                possible_times = [start_time for start_time in times
                                  if (start_time + max_runtime) < shadow_time]
                for start_time in possible_times:
                    if allocator.can_run_now(backfill_task.requirements,
                                             start_time):
                        allocs = allocator.allocate(backfill_task.requirements,
                                                    start_time)
                        backfill_task.allocations = allocs
                # Could not backfill this task
                if not backfill_task.allocations:
                    remaining.append(backfill_task)
            # Tasks in remaining cannot be backfilled and must be run later
            # Reset the tasks to the remaining list
            tasks = remaining


class AlgorithmLogWrapper:
    """Algorithm log wrapper class.

    Algorithm wrapper class to be used as a wrap to log the task scheduling
    data for future training and other extra information.
    """

    def __init__(self, cls, alloc_logfile='schedule_log.txt', **kwargs):
        """Algorithm log wrapper class constructor.

        Algorithm wrapper class constructor.
        :param cls: object to pass operations onto
        :type cls: algorithm object
        :param alloc_logfile: name of logfile to write task scheduling to
        :type alloc_logfile: str
        :param kwargs: key word arguments to pass to schedule_all()
        :type kwargs: instance of dict
        """
        self.cls = cls
        self.alloc_logfile = alloc_logfile
        self.kwargs = kwargs

    def schedule_all(self, tasks, resources):
        """Schedule all tasks using the internal class and log results.

        Schedule all of the tasks with the internal class and write the
        results out to a log file.
        """
        self.cls.schedule_all(tasks, resources, **self.kwargs)
        # Make the directory, just in case it doesn't exist already
        os.makedirs(os.path.dirname(self.alloc_logfile), exist_ok=True)
        with open(self.alloc_logfile, 'a', encoding='utf-8') as fp:
            print('; Log start at', time.time(), file=fp)
            # curr_allocs = []
            for task in tasks:
                # TODO: Rethink this log output

                # possible_allocs = build_allocation_list(task, tasks,
                #                                         resources,
                #                                         curr_allocs)
                # Find the value of a - the index of the allocation for this
                # task
                # a = -1
                # TODO: Calculation of a needs to change
                # if task.allocations:
                #     start_time = task.allocations[0].start_time
                #     # a should be the first alloc with the same start_time
                #     for i, alloc in enumerate(possible_allocs):
                #         if alloc[0].start_time == start_time:
                #             a = i
                #             break
                # Output in SWF format
                # TODO: These variables may not be all in the right spot and
                # some may be missing as well
                print(-1, -1, -1, task.requirements.max_runtime,
                      task.requirements.nodes, task.requirements.max_runtime,
                      task.requirements.mem_per_node, task.requirements.nodes,
                      -1, task.requirements.mem_per_node,
                      task.requirements.mem_per_node, -1,
                      # task.requirements.mem, task.requirements.nodes, -1,
                      # task.requirements.mem, task.requirements.mem, -1,
                      -1, -1, -1, -1, -1, -1, -1, file=fp)
                # print(*vec, file=fp)
                # curr_allocs.extend(task.allocations)


# TODO: Perhaps this value should be a config value
MEDIAN = 2


algorithm_objects = {
    'fcfs': FCFS,
    'backfill': Backfill,
    'sjf': SJF,
}


def load(algorithm=None, **kwargs):  # noqa ('algorithm' may be used in the future)
    """Load data needed by the algorithms.

    Load data needed by algorithms, if necessary.
    """
    FCFS.load(**kwargs)
    Backfill.load(**kwargs)
    SJF.load(**kwargs)


def choose(algorithm=None, default_algorithm=None, **kwargs):
    """Choose which algorithm to run at this point.

    Determine which algorithm class needs to run and return it.
    :param tasks: list of tasks:
    :type tasks: list of instance of Task
    :rtype: class derived from Algorithm (not an instance)
    """
    # Choose the default algorithm
    default = default_algorithm if default_algorithm is not None else 'fcfs'
    cls = algorithm_objects[default]
    if algorithm is not None:
        cls = algorithm_objects[algorithm]
    return AlgorithmLogWrapper(cls, **kwargs)
# Ignoring E0211: This is how the class is designed right now, we should think about changing this
#                 however.
# Ignoring W0511: A number of these TODO's are hinted at in issue #333, but I don't want to remove
#                 them from the code until this issue is fully addressed.
# Ignoring R0903: Too few public methods, not sure how this calculated and this will be fixed with
#                 issue #333
# pylama:ignore=E0211,C0415,W0511,R0903
