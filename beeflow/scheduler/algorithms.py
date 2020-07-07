"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import time

# import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types


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
        # See https://www.cse.huji.ac.il/~perf/ex11.html
        # TODO: This time may be invalidated if the algorithm
        # takes too long
        current_time = int(time.time())
        immediate_allocations = []
        later_allocations = []
        tasks = tasks[:]
        # Jobs that must run later or be backfilled
        later = []
        # Allocate free resources for the first jobs in the list
        # so that they can run immediately
        while tasks:
            task = tasks.pop(0)
            total = sched_types.Resource.calculate_remaining(
                resources, immediate_allocations)
            # Check if it can run
            if not total.empty and total.runs(task):
                # Allocate the job if there are enough total resources
                allocs = Backfill._allocate_aggregate(resources,
                                                      immediate_allocations,
                                                      task, current_time)
                immediate_allocations.extend(allocs)
                task.allocations = allocs
            else:
                # This must run later or be backfilled
                later.append(task)
        # Allocate jobs that need more than the required resources
        # and must run later
        backfill = []
        while later:
            task = later.pop(0)
            # Check if this job needs more resources than available
            total = sched_types.Resource.calculate_remaining(
                resources, immediate_allocations)
            if not total.runs(task):
                allocations = []
                allocations.extend(immediate_allocations)
                allocations.extend(later_allocations)
                # Determine when this job can start
                start_time = Backfill._calculate_earliest_start_time(
                    resources, immediate_allocations, later_allocations, task)
                allocs = Backfill._allocate_aggregate(resources,
                                                      allocations,
                                                      task, start_time)
                # Allocate a later time job
                later_allocations.extend(allocs)
                task.allocations = allocs
            else:
                # This task may be backfilled
                backfill.append(task)
        # Now start to backfill with all remaining tasks
        while backfill:
            task = backfill.pop(0)
            # Check if the job doesn't use more than what is available
            # and will stop before other scheduled jobs
            total = sched_types.Resource.calculate_remaining(
                resources, immediate_allocations)
            if total.runs(task):
                empty_time = Backfill._calculate_empty_time(
                    resources, immediate_allocations, later_allocations, task)
                if task.requirements['max_runtime'] <= empty_time:
                    # Backfill it
                    allocs = Backfill._allocate_aggregate(
                        resources, immediate_allocations, task, current_time)
                    immediate_allocations.extend(allocs)
                    task.allocations = allocs
                else:
                    # This task must run later
                    # TODO: Runtime
                    start_time = Backfill._calculate_earliest_start_time(
                        resources, immediate_allocations, later_allocations,
                        task)
                    allocs = Backfill._allocate_aggregate(
                        resources, immediate_allocations, task, start_time)
                    later_allocations.extend(allocs)
                    task.allocations = allocs

    @staticmethod
    def _calculate_empty_time(resources, immediate_allocations,
                              later_allocations, task):
        """Calculate the "empty time".

        This calculates the max amount of time a task could run
        if allocated in a currently empty slot.
        :param resources:
        :type later_allocations:
        :param immediate_allocations:
        :type immediate_allocations:
        :param later_allocations:
        :type later_allocations:
        :param task:
        :type task:
        :rtype: int
        """
        immediate_allocations = immediate_allocations[:]
        later_allocations = later_allocations[:]
        later_allocations.sort(key=lambda a: a.start_time)
        current_time = int(time.time())
        for allocation in later_allocations:
            immediate_allocations.append(allocation)
            total = sched_types.Resource.calculate_remaining(
                resources, immediate_allocations)
            if total.runs(task):
                return (allocation.start_time + allocation.max_runtime
                        - current_time)
        return 0

    @staticmethod
    def _calculate_earliest_start_time(resources, immediate_allocations,
                                       later_allocations, task):
        """Calulate the earliest start time for a task.

        Calculate the earliest possible start time for a task.
        :param resources:
        :type resources:
        :param immediate_allocations:
        :type immediate_allocations:
        :param later_allocations:
        :type later_allocations:
        :param task:
        :type task:
        :rtype: int
        """
        immediate_allocations = immediate_allocations[:]
        later_allocations = later_allocations[:]
        later_allocations.sort(key=lambda a: (a.start_time + a.max_runtime))
        for allocation in later_allocations:
            immediate_allocations.append(allocation)
            total = sched_types.Resource.calculate_remaining(
                resources, immediate_allocations)
            # Return the time if it runs with this task added
            if total.runs(task):
                return allocation.start_time + allocation.max_runtime
        return -1

    @staticmethod
    def _allocate_aggregate(resources, allocations, task, start_time):
        """Allocate a list of resources based on the task.

        Allocate a list of resources that are needed by the task
        for the given time.
        :param resources: available resources
        :type resources: list of instance of Resource
        :param allocations: current allocations
        :type allocations: list of instance of Allocation
        :param task: task needing allocation
        :type task: instance of Task
        :param start_time: start time of task (seconds since epoch)
        :type start_time: int
        :rtype: list of instance of Allocation
        """
        task_allocated = []
        for resource in resources:
            # TODO
            allocs = [a for a in allocations if a.id_ == resource.id_]
            fit = sched_types.Resource.fit_remaining(resource, allocs,
                                                     task_allocated, task)
            if fit is not None:
                fit.start_time = start_time
                fit.max_runtime = task.requirements['max_runtime']
                task_allocated.append(fit)
        return task_allocated
