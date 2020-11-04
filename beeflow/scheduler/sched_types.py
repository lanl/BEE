"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""
import abc


class Serializable(abc.ABC):
    """Serializable base class.

    This class allows subclasses to easily serialize into simple Python
    data types which can be serialized into JSON.
    """

    @abc.abstractmethod
    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        return self.__dict__

    @staticmethod
    @abc.abstractmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """


class Task(Serializable):
    """Representation of a Task and its various requirements.

    This class represents the task as a set of resource requirements
    which can be used by the scheduling algorithm to easily determine
    the best allocation.
    """

    def __init__(self, workflow_name, task_name, requirements=None,
                 allocations=None):
        """Task constructor.

        Create a new Task with given parameters.
        :param workflow_name: name of the workflow
        :type workflow_name: str
        :param task_name: name of the task
        :type task_name: str
        :param requirements: requirements dict
        :type requirements: dict of requirements
        :param allocations: list of current allocations
        :type allocations: list of instance of Allocation
        """
        self.workflow_name = workflow_name
        self.task_name = task_name
        self.requirements = (RequirementBase(**requirements)
                             if requirements is not None else {})
        self.requirements
        self.allocations = allocations if allocations is not None else []

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        result = dict(self.__dict__)
        if 'allocations' in result and result['allocations']:
            result['allocations'] = [alloc.encode()
                                     for alloc in result['allocations']]
        # TODO: Requirements could also add an encode() message
        if 'requirements' in result and result['requirements']:
            result['requirements'] = result['requirements'].__dict__
        return result

    @staticmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
        data = dict(data)
        return Task(**data)


class Resource(Serializable):
    """Resource base class.

    Resource base class.
    """

    def __init__(self, id_=None, nodes=1, mem_per_node=8192, gpus_per_node=0):
        """Resource base constructor.

        Resource base constructor.
        """
        self.id_ = id_
        self.nodes = nodes
        self.mem_per_node = mem_per_node
        self.gpus_per_node = gpus_per_node

    def can_allocate(self, requirements):
        """Check if this resource can even be allocated for these requirements.

        If this resource cannot provide certain properties that are required,
        then it cannot be allocated for the given task. For example, if a
        number of gpus are required, but this resource has none, then no nodes
        should be allocated.
        :param requirements: allocation requirements to check
        :type requirements: instance of RequirementBase
        """
        return (requirements.gpus_per_node == 0
                or (self.gpus_per_node >= requirements.gpus_per_node))
        #return (requirements.gpus == 0 or (requirements.gpus > 0
        #                                   and self.gpus > 0))

    def fits_requirements(self, requirements):
        """Check the resource against a set of requirements.

        Check this resource against the requirements.
        :param requirements: requirements to match against
        :type requirements: instance of RequirementBase
        :rtype: bool
        """
        return (requirements.nodes <= self.nodes
                and requirements.mem_per_node <= self.mem_per_node
                and requirements.gpus_per_node <= self.gpus_per_node)

    def allocate(self, remaining, task_allocated, requirements, start_time):
        """Return the largest needed new allocation.

        Create the largest possible new allocation, given current allocations
        and the requirement.
        :param remaining: remaining unused part of resource
        :type remaining: instance of Resource
        :param task_allocated: allocations for the task
        :type task_allocated: list of instance of Allocation
        :param requirements: requirements to allocate for
        :type requirements: instance of RequirementBase
        :param start_time: start time
        :type start_time: int
        :rtype:
        """
        total_task_allocated = rsum(*task_allocated)
        nodes = (remaining.nodes
                 if (remaining.nodes
                     <= (requirements.nodes - total_task_allocated.nodes))
                 else (requirements.nodes - total_task_allocated.nodes))
        #mem = (remaining.mem
        #       if (remaining.mem
        #           <= (requirements.mem - total_task_allocated.mem))
        #       else (requirements.mem - total_task_allocated.mem))
        #gpus = (remaining.gpus
        #        if (remaining.gpus
        #            <= (requirements.gpus - total_task_allocated.gpus))
        #        else (requirements.gpus - total_task_allocated.gpus))

        # Note: self.mem_per_node and self.gpus_per_node are used here instead
        # of remaining.mem_per_node and remaining.gpus_per_node
        return Allocation(start_time=start_time,
                          max_runtime=requirements.max_runtime, id_=self.id_,
                          nodes=nodes, mem_per_node=self.mem_per_node,
                          gpus_per_node=self.gpus_per_node)

    @property
    def empty(self):
        """Determine if the resource class is empty.

        Property which determines whether or not a resource is empty.
        :rtype: bool
        """
        #return self.nodes == 0 or self.mem == 0
        return self.nodes == 0

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        result = dict(self.__dict__)
        return result

    @staticmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
        data = dict(data)
        return Resource(**data)


def diff(resource1, resource2):
    """Calculate the difference between two resources.

    Calculate the difference between two resources.
    :param resource1: first resource
    :type resource1: instance of Resource
    :param resource2: second resource
    :type resource2: instance of Resource
    :rtype: new instance of Resource
    """
    return Resource(nodes=resource1.nodes-resource2.nodes,
                    mem_per_node=max(resource1.mem_per_node,
                                     resource2.mem_per_node),
                    gpus_per_node=max(resource1.gpus_per_node,
                                      resource2.gpus_per_node))
                    #mem_per_node=abs(resource1.mem_per_node
                    #                 -resource2.mem_per_node),
                    #gpus_per_node=abs(resource1.gpus_per_node
                    #                  -resource2.gpus_per_node))


def rsum(*resources):
    """Calculate a sum of resources in a list.

    Calculate a sum of all the resources in a list.
    :param resources:
    :type resources:
    :rtype: new instance of Resource
    """
    if not resources:
        return Resource(nodes=0, mem_per_node=0, gpus_per_node=0)
    return Resource(nodes=sum(r.nodes for r in resources),
                    mem_per_node=max(r.mem_per_node for r in resources),
                    gpus_per_node=max(r.gpus_per_node for r in resources))
                    #mem=sum(r.mem for r in resources),
                    #gpus=sum(r.gpus for r in resources))


class RequirementsError(Exception):
    """Requirements Error class.

    Class for storing requirements.
    """

    def __init__(self, msg):
        """Initialize the requirements error.

        Requirements error constructor.
        :param msg: a message
        :type msg: str
        """
        self.msg = msg


class RequirementBase:
    """Base requirements class.

    Base requirements class.
    """

    def __init__(self, max_runtime=1, nodes=1, mem_per_node=1024, gpus_per_node=0, cost=1):
        """Constructor for requirements.

        Constructor for requirements.
        :param nodes: number of nodes
        :type nodes: int
        """
        if nodes < 0:
            raise RequirementsError('Invalid "nodes" requirement of %i'
                                    % nodes)
        self.nodes = nodes
        if mem_per_node < 0:
            raise RequirementsError('Invalid "mem_per_node" requirement of %i'
                                    % mem)
        self.mem_per_node = mem_per_node
        if gpus_per_node < 0:
            raise RequirementsError('Invalid "gpus_per_node" requirement of %i'
                                    % gpus)
        self.gpus_per_node = gpus_per_node
        if max_runtime < 0:
            raise RequirementsError('Invalid "max_runtime" requirement of %i'
                                    % max_runtime)
        self.max_runtime = max_runtime
        self.cost = cost


class Allocation(Resource):
    """Class representing a resource allocation.

    This respresents a resource dedicated to a particular
    task or workflow.
    """

    def __init__(self, start_time=None, max_runtime=None, **kwargs):
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
        super().__init__(**kwargs)
        self.start_time = start_time if start_time is not None else 0
        self.max_runtime = max_runtime

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        return self.__dict__

    @staticmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
        return Allocation(**data)
