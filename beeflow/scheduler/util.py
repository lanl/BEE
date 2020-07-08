"""BEE Scheduler utility functions.

Utility functions for the scheduler component.
"""
import beeflow.scheduler.sched_types as sched_types


def calculate_remaining(resources, allocations):
    """Calculate the remaining resources.

    Calculate a total of remaining resources available.
    :param resources: current resources
    :type resources: list of instance of Resource
    :param allocations: current allocations
    :type allocations: list of instance of Allocation
    :rtype: instance of Allocation
    """
    # TODO: Update this to include info about other resource types
    cores = (sum(r.cores for r in resources)
             - sum(a.cores for a in allocations))
    # This Allocation returned should not have anything meaningful
    # for id_, nor for start_time and max_runtime
    return sched_types.Allocation(id_=None, cores=cores)


def allocate_aggregate(resources, allocations, task, start_time):
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
        fit = resource.fit_remaining(allocs, task_allocated, task, start_time,
                                     task.requirements['max_runtime'])
        if fit is not None:
            task_allocated.append(fit)
        # Check if it has enough
        allocated = calculate_remaining(task_allocated, [])
        if allocated.runs(task):
            break
    return task_allocated


def calculate_overlap(allocations, start_time, max_runtime):
    """Calculate allocation overlap for a specifc time period.

    Return a list of overlapping allocations for a certain time
    period.
    :param allocations: all allocations
    :type allocations: list of instance of Allocation
    :param start_time: start time
    :type start_time: int
    :param max_runtime: maximum runtime
    :type max_runtime: int
    :rtype: list of instance of Allocation
    """
    # TODO
    return [a for a in allocations
            if start_time < (a.start_time + a.max_runtime)
            and (start_time + max_runtime) > a.start_time]
