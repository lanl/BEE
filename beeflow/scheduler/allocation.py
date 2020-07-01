"""Allocation code for storing task and workflow resource information.

Code for holding allocation details for various tasks/jobs and
workflows (such as number of nodes, partitions, and other more
specific resource details).
"""

import beeflow.scheduler.sched_types as sched_types


class Allocation:
    """Class representing a resource allocation.

    This respresents a set of resources dedicated to a particular
    task or workflow.
    """

    def __init__(self, workflow_name, task_name, resources=None):
        """Allocation constructor.

        Initialize an allocation constructor to store information
        about particular resources allocated to a task or workflow.
        :param workflow_name: workflow name
        :type workflow_name: str
        :param task_name: task name
        :type task_name: str
        :param resources: list of allocated resources
        :type resources: list of instance of ResourceSubset
        """
        self.workflow_name = workflow_name
        self.task_name = task_name
        self.resources = resources if resources is not None else []


class AllocationStore:
    """Store of allocation information for a session.

    Class for storing main records of resource allocations
    for different tasks/jobs and workflows.
    """

    def __init__(self, allocations=None):
        """Allocation Store constructor.

        Constructor for an AllocationStore.
        :param allocations: a list of allocations
        :type allocations: a list of instance of Allocation
        """
        self.allocations = allocations if allocations is not None else []
        self.completed = []

    def schedule(self, algorithm, task, tasks, resources):
        """Schedule a task with a specific algorithm on a set of clusters.

        Schedule a task using this algorithm on a set of clusters (the
        highest available resource level).
        :param algorithm: algorithm base class
        :type algorithm:
        :param task: task to schedule
        :type task: instance of Task
        :param resources: list of resources to use
        :type resources: list of instance of ResourceCollection
        """
        alloc = algorithm.schedule(task, tasks, resources, self.allocations)
        if alloc is not None:
            self.allocations.append(alloc)
        return alloc
        # TODO

    def update_allocation(self, task):
        """Update a task allocation.

        Update a task that has already been scheduled. Check the
        status of the task to see if it has completed.
        :param task: task to update
        :type task: instance of Task
        """
        # Remove completed tasks and add them to the completed list
        if task.status == sched_types.TaskStatus.COMPLETED:
            task_i = None
            # Find the task allocation
            for i, alloc in enumerate(self.allocations):
                if (alloc.workflow_name == task.workflow_name
                        and alloc.task_name == task.task_name):
                    task_i = i
                    break
            if task_i is not None:
                self.completed.append(self.allocations[task_i])
                del self.allocations[task_i]
