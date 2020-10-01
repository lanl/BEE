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
    resource_total = sched_types.rsum(*resources)
    resource_allocated = sched_types.rsum(*allocations)
    return sched_types.diff(resource_total, resource_allocated)


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
        total_used = sched_types.rsum(*[a for a in allocations
                                        if a.id_ == resource.id_])
        remaining = sched_types.diff(resource, total_used)
        if not remaining.empty:
            # Allocate a new resource
            alloc = resource.allocate(remaining, task_allocated,
                                      task.requirements, start_time=start_time)
            task_allocated.append(alloc)
        total_allocated = sched_types.rsum(*task_allocated)
        # Check if the allocation has been completed
        if total_allocated.fits_requirements(task.requirements):
            break
    return task_allocated


def calculate_overlap(allocations, start_time, max_runtime):
    """Calculate allocation overlap for a specifc time period.

    Return a list of overlapping allocations for a given certain time
    period.
    :param allocations: all allocations
    :type allocations: list of instance of Allocation
    :param start_time: start time
    :type start_time: int
    :param max_runtime: maximum runtime
    :type max_runtime: int
    :rtype: list of instance of Allocation
    """
    return [a for a in allocations
            if start_time < (a.start_time + a.max_runtime)
            and (start_time + max_runtime) > a.start_time]
