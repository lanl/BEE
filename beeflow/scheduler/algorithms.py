"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import time
import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types


class FCFS:
    """FCFS class static methods.

    This class holds static methods used internally by the FCFS
    scheduling algorithm.
    """

    @staticmethod
    def schedule(task, tasks, resources, allocations):
        """Run a first-come first-serve algorithm.

        Run FCFS and determine the best next allocation
        for the given task or return None if there is no
        allocation spots available.
        :param task: task to schedule
        :type task: instance of Task
        :param resources: list of resources to utilize
        :type resources: list of instance of Resource
        :param allocations: list of already allocated resources and tasks
        :type allocations: list of instance of Allocation
        :rtype: instance of Allocation
        """
        # TODO: Handle collection of resources spread across different
        # collections/groups
        for resource in resources:
            resource_subset, min_start_time = FCFS.fit(task, tasks, resource,
                                                       allocations)
            if resource_subset is not None:
                task.start_time = min_start_time
                return allocation.Allocation(workflow_name=task.workflow_name,
                                             task_name=task.task_name,
                                             resources=[resource_subset])
        return None

    @staticmethod
    def fit(task, tasks, resource, allocations):
        """Fit a resource to a task.

        Return a ResourceSubset if a task can "fit" or run on this resource
        collection and return None otherwise.
        :param task: task to fit
        :type task: instance of Task
        :param tasks: list of all tasks
        :type tasks: list of instance of Task
        :param resource: resource to test against the task
        :type resource: instance of ResourceCollection
        :param allocations: current completed allocations list
        :type allocations: list of instance of Allocation
        :rtype: instance of ResourceSubset or None
        """
        # TODO: Check other allocations
        # TODO: Add in task requirements
        if resource.cores >= task.requirements.max_cores:
            resource_subset = sched_types.ResourceSubset(
                id_=resource.id_, cores=task.requirements.max_cores),
            # TODO: This time is not accurate
            min_start_time = int(time.time())
            return resource_subset, min_start_time
        return None, None
