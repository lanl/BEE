"""Task allocator code."""
from beeflow.scheduler import serializable


class TaskAllocator:
    """Task allocator class.

    Class used to help manage allocation of tasks onto multiple resources.
    """

    def __init__(self, resources):
        """Task allocator constructor.

        :param resources: available resources that can be allocated
        :type resources: list of instance of Resource
        """
        self.allocations = []
        self.resources = resources

    def _fits_requirements_with_overlap(self, reqs, overlap):
        """Check if a task with these requirements can run with overlap.

        This determines if a task can run given `overlap`, a list of
        overlapping allocations.
        :param reqs: task requirements
        :type reqs: instance of Requirements
        :param overlap: overlappinig allocations
        :type overlap: list of instance of Allocation
        :rtype: bool
        """
        total_nodes = 0
        # Count the total number of nodes that match the required properties
        for res in self.resources:
            # TODO: Handle shared nodes (perhaps with a shared option)
            allocs = [alloc for alloc in overlap if alloc.id_ == res.id_]
            # if (reqs.mem_per_node <= res.mem_per_node
            #     and reqs.gpus_per_node <= res.gpus_per_node):
            if res.fits(reqs):
                total_nodes += (res.nodes - sum(alloc.nodes for alloc in allocs))
        # Return True if we have enough nodes that match
        return total_nodes >= reqs.nodes

    def _calculate_overlap(self, start_time, max_runtime):
        """Calculate the overlap for the time period [start_time, max_runtime].

        :param start_time: start time of the period
        :type start_time: int
        :param max_runtime: max runtime for the time period
        :type max_runtime: int
        :rtype: list of instance of Allocation
        """
        # TODO: This calculation be off
        return [alloc for alloc in self.allocations
                if (start_time < (alloc.start_time + alloc.max_runtime)
                    and (start_time + max_runtime) > alloc.start_time)]

    def fits_requirements(self, reqs):
        """Determine if the resources can fit the requirements given.

        :param reqs: requirements
        :type reqs: instance of Requirements
        :rtype: bool
        """
        return self._fits_requirements_with_overlap(reqs, [])

    def can_run_now(self, reqs, start_time):
        """Determine if a task with the requirements can run at start_time.

        :param reqs: requirements of a task
        :type reqs: instance of Requirements
        :param start_time: start time of a task
        :type start_time: int
        :rtype: bool
        """
        # Calculate the overlapping allocations
        overlap = self._calculate_overlap(start_time, reqs.max_runtime)
        return self._fits_requirements_with_overlap(reqs, overlap)

    def get_next_end_time(self, start_time):
        """Return the next finish time after start_time.

        This returns the next finish time of the current allocations stored in
        the allocator. If no finish time after this start_time exists then
        start_time will just be returned.
        :param start_time: start time of a possible task
        :type start_time: int
        """
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
        :param reqs: task requirements
        :type reqs: instance of Requirements
        :param start_time: start time of the task allocation
        :type start_time: int
        :rtype: list of instance of Allocation
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
            # if (reqs.mem_per_node <= res.mem_per_node
            #     and reqs.gpus_per_node <= res.gpus_per_node):
            if res.fits(reqs):
                used_nodes = sum(alloc.nodes for alloc in other_allocs)
                avail_nodes = res.nodes - used_nodes
                if avail_nodes > 0:
                    nodes = reqs.nodes - total_nodes
                    nodes = nodes if nodes < avail_nodes else avail_nodes
                    total_nodes += nodes
                    # Allocations should just contain a reference to the
                    # resource, by id_, rather than duplicating all the
                    # properties
                    alloc = Allocation(id_=res.id_, start_time=start_time,
                                       max_runtime=reqs.max_runtime,
                                       nodes=nodes)
                    allocs.append(alloc)
        # Add the new allocations to the stored allocations
        self.allocations.extend(allocs)
        return allocs


class Resource(serializable.Serializable):
    """Resource class.

    Resource class representing a resource.
    """

    def __init__(self, id_, nodes=1, mem_per_node=8192, gpus_per_node=0):
        """Resource class constructor.

        :param id_: ID of the resource
        :type id_: str
        :param nodes: number of nodes
        :type nodes: int
        :param mem_per_node: amount of memory
        :type mem_per_node: int
        :param gpus_per_node: number of GPUs per node
        :type gpus_per_node: int
        """
        self.id_ = id_
        self.nodes = nodes
        self.mem_per_node = mem_per_node
        self.gpus_per_node = gpus_per_node

    def fits(self, reqs):
        """Return True if the requirements fit this resource.

        :param reqs: task requirements
        :type reqs: instance of Requirements
        :rtype: bool
        """
        return (reqs.mem_per_node <= self.mem_per_node
                and reqs.gpus_per_node <= self.gpus_per_node)

    @staticmethod
    def decode(data):
        """Decode the resource.

        :param data: data representing the resource
        :type data: dict
        """
        return Resource(**data)


class Requirements(serializable.Serializable):
    """Requirements class.

    Requirements class representing task requirements.
    """

    # TODO: Determine default requirements
    def __init__(self, max_runtime, nodes=1, mem_per_node=1024,
                 gpus_per_node=0, cost=1):
        """Construct a requirements object.

        :param max_runtime: maximum runtime in seconds
        :type max_runtime: int
        :param nodes: number of nodes in total
        :type nodes: int
        :param mem_per_node: amount of memory per node
        :type mem_per_node: int
        :param gpus_per_node: number of gpus per node
        :type gpus_per_node: int
        :param cost: cost value
        :type cost: float
        """
        self.max_runtime = max_runtime
        self.nodes = nodes
        self.mem_per_node = mem_per_node
        self.gpus_per_node = gpus_per_node
        # TODO: Determine what other requirement properties are needed
        # TODO: Determine what the cost should be and how it is computed
        self.cost = cost

    @staticmethod
    def decode(data):
        """Decode the requirements.

        :param data: data representing the requirements
        :type data: dict
        """
        return Requirements(**data)


class Allocation(serializable.Serializable):
    """Allocation class.

    This represents an allocation for a task on a single resource.
    """

    def __init__(self, id_, start_time, max_runtime, nodes):
        """Allocation constructor.

        :param id_: ID of the resource
        :type id_: str
        :param start_time: start time of the allocation (seconds)
        :type start_time: int
        :param max_runtime: maximum runtime of the allocation (seconds)
        :type max_runtime: int
        :param nodes: number of nodes allocated
        :type nodes: int
        """
        self.id_ = id_
        self.start_time = start_time
        self.max_runtime = max_runtime
        # TODO: Determine what other allocation properties are needed (other
        # than just nodes)
        self.nodes = nodes

    @staticmethod
    def decode(data):
        """Decode the allocation.

        :param data: data representing the allocation
        :type data: dict
        """
        return Allocation(**data)

# Ignore W0511: This allows us to have TODOs in the code
# pylama:ignore=W0511
