"""Task allocator code.

"""

# TODO: Remove this import when the Allocation, Resource and Requirements
# clases have been implemented here
import beeflow.scheduler.sched_types as sched_types


class TaskAllocator:
    """Task allocator class.

    Class used to help manage allocation of tasks onto multiple resources.
    """

    def __init__(self, resources):
        """Task allocator constructor.

        :param resources: available resources that can be allocated
        :type resources: list of instance of sched_types.Resource
        """
        self.allocations = []
        self.resources = resources
        # TODO

    def _fits_requirements_with_overlap(self, reqs, overlap):
        """Check if a task with these requirements can run with overlap.

        This determines if a task can run given `overlap`, a list of
        overlapping allocations.
        :param reqs: task requirements
        :type reqs: instance of sched_types.RequirementsBase
        :param overlap: overlappinig allocations
        :type overlap: list of instance of sched_types.Allocation
        :rtype: bool
        """
        # TODO
        total_nodes = 0
        # Count the total number of nodes that match the required properties
        for res in self.resources:
            # TODO: Handle shared nodes (perhaps with a shared option)
            allocs = [alloc for alloc in overlap if alloc.id_ == res.id_]
            if (reqs.mem_per_node <= res.mem_per_node
                and reqs.gpus_per_node <= res.gpus_per_node):
                total_nodes += (res.nodes
                                - sum(alloc.nodes for alloc in allocs))
        # Return True if we have enough nodes that match
        return total_nodes >= reqs.nodes

    def fits_requirements(self, reqs):
        """Determine if the resources can fit the requirements given.

        :param reqs: requirements
        :type reqs: instance of sched_types.RequirementsBase
        :rtype: bool
        """
        return self._fits_requirements_with_overlap(reqs, [])
        """
        total_nodes = 0
        # Count the total number of nodes that match the required properties
        for res in self.resources:
            if (reqs.mem_per_node <= res.mem_per_node
                and reqs.gpus_per_node <= res.gpus_per_node):
                total_nodes += res.nodes
        # Return True if we have enough nodes that match
        return total_nodes >= reqs.nodes
        """

    def _calculate_overlap(self, start_time, max_runtime):
        """Calculate the overlap for the time period [start_time, max_runtime].

        :param start_time: start time of the period
        :type start_time: int
        :param max_runtime: max runtime for the time period
        :type max_runtime: int
        :rtype: list of instance of sched_types.Allocation
        """
        return [alloc for alloc in self.allocations
                if (start_time < (alloc.start_time + alloc.max_runtime)
                    and (start_time + max_runtime) > alloc.start_time)]


    def can_run_now(self, reqs, start_time):
        """Determine if a task with the requirements can run at start_time.

        :param reqs: requirements of a task
        :type reqs: instance of sched_types.RequirementsBase
        :param start_time: start time of a task
        :type start_time: int
        :rtype: bool
        """
        # Calculate the overlapping allocations
        overlap = self._calculate_overlap(start_time, reqs.max_runtime)
        #overlap = [alloc for alloc in self.allocations
        #           if start_time < (alloc.start_time + alloc.max_runtime)
        #           and (start_time + max_runtime) > alloc.start_time]
        return self._fits_requirements_with_overlap(reqs, overlap)
        # TODO

    def get_next_end_time(self, start_time):
        """Return the next finish time after start_time.

        This returns the next finish time of the current allocations stored in
        the allocator. If no finish time after this start_time exists then
        start_time will just be returned.
        :param start_time: start time of a possible task
        :type start_time: int

        The event times are the set of times (in seconds) of all the allocated start times and finish times of tasks. For example if occur anytime a task allocation starts or finishes. For example if a 
        """
        #if not self.allocations:
        #    end_time = start_time
        #else:
        #    min(a.start_time + a.max_runtime for a in self.allocations)

        #end_time = start_time
        # end_times = [a.start_time + a.max_runtime for a in self.allocations]
        end_times = self.get_end_times()
        for end_time in end_times:
            if end_time > start_time:
                return end_time
        return start_time

    def get_end_times(self):
        """Get a list of ending times for all allocations.

        :rtype: list of int
        """
        # End times should be unique
        return list(set(a.start_time + a.max_runtime
                        for a in self.allocations))

    def allocate(self, reqs, start_time):
        """Allocate some allocations meeting the requirements at start_time.

        Note: This assumes that this allocation can be made and that there are
        no other overlapping allocations that could conflict.
        :param reqs:
        :type reqs:
        :param start_time:
        :type start_time:
        :rtype: list of instance of sched_types.Allocation
        """
        # TODO
        overlap = self._calculate_overlap(start_time, reqs.max_runtime)
        allocs = []
        # Total number of nodes already allocated
        total_nodes = 0
        for res in self.resources:
            if total_nodes >= reqs.nodes:
                # Stop when we have enough nodes scheduled
                break
            other_allocs = [alloc for alloc in overlap if alloc.id_ == res.id_]
            # TODO: Replace this with a method res.fits()
            if (reqs.mem_per_node <= res.mem_per_node
                and reqs.gpus_per_node <= res.gpus_per_node):
                used_nodes = sum(alloc.nodes for alloc in other_allocs)
                avail_nodes = res.nodes - used_nodes
                if avail_nodes > 0:
                    nodes = reqs.nodes - total_nodes
                    nodes = nodes if nodes < avail_nodes else avail_nodes
                    total_nodes += nodes
                    # TODO: Allocations should just contain a reference to the
                    # resource, rather than duplicating all the properties
                    alloc = sched_types.Allocation(
                        id_=res.id_, start_time=start_time,
                        max_runtime=reqs.max_runtime, nodes=nodes,
                        mem_per_node=res.mem_per_node,
                        gpus_per_node=res.gpus_per_node)
                    allocs.append(alloc)
        # Add the new allocations to the stored allocations
        self.allocations.extend(allocs)
        return allocs


class Resource:
    """
    """

    def __init__(self):
        """
        """
        # TODO


class Requirements:
    """
    """

    def __init__(self):
        """
        """
        # TODO


class Allocation:
    """
    """

    def __init__(self, id_, start_time, max_runtime, nodes):
        """
        """
        # TODO
