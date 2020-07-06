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
    def schedule_all(tasks, resources):
        """Schedule a list independent tasks.

        Schedule an entire list of tasks using FCFS. Tasks that
        cannot be allocated will be left with allocations properties.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of Resource
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
                    alloc = sched_types.Allocation(id_=resource.id_,
                        cores=cores, start_time=start_time,
                        max_runtime=task.requirements['max_runtime'])
                    allocations.append(alloc)
                    # TODO: Handle multiple resource allocations for a task
                    task.allocations = [alloc]
                    break
