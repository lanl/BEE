"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""
import abc
import enum
import time


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
        :param workflow_name:
        :type workflow_name:
        :param task_name:
        :type task_name:
        :param requirements:
        :type requirements:
        :param allocations:
        :type allocations:
        """
        self.workflow_name = workflow_name
        self.task_name = task_name
        self.requirements = requirements if requirements is not None else {}
        self.allocations = allocations if allocations is not None else []

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        result = dict(self.__dict__)
        if 'allocations' in result and result['allocations']:
            result['allocations'] = [alloc.encode()
                                     for alloc in result['allocations']]
        return result

    @staticmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
        data = dict(data)
        return Task(**data)


# TODO: Add a generic way to add resource types to a ResourceCollection
class Resource(Serializable):
    """Resource collection class.

    Generic class for holding a collection of resources.
    """

    def __init__(self, id_, cores=1):
        """Resource collection constructor.

        Initialize a new ResourceCollection object with resource details.
        :param id_: id of the resource
        :type id_: str
        :param cores: number of cores contained in the resource
        :type cores: int
        """
        self.id_ = id_
        self.cores = cores

    def runs(self, task):
        """Determine if the task can run on this resource.

        Compare the requirements of the task with the details
        of this resource and returns True if this task can run
        on this resource and False otherwise.
        :param task: task to check
        :type task: instance of Task
        """
        # TODO: Check more requirements
        if ('cores' in task.requirements
                and task.requirements['cores'] > self.cores):
            # Too many cores required
            return False
        return True

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
        return Resource(**data)


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
        self.start_time = (start_time if start_time is not None
                           else int(time.time()))
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
