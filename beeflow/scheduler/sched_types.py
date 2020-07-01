"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""
import enum


class Task:
    """Representation of a Task and its various requirements.

    This class represents the class as a set of resource requirements
    which can be used by the scheduling algorithm to easily determine
    the best allocation.
    """

    def __init__(self, workflow_name, task_name, max_runtime,
                 requirements=None, start_time=None, resources=None):
        """Task constructor.

        Create a new Task with given parameters.
        :param workflow_name:
        :type workflow_name:
        :param task_name:
        :type task_name:
        :param max_runtime:
        :type max_runtime:
        :param requirements:
        :type requirements:
        :param start_time:
        :type start_time:
        :param resources:
        :type resources:
        """
        self.workflow_name = workflow_name
        self.task_name = task_name
        self.max_runtime = max_runtime
        self.requirements = requirements
        if requirements is None:
            self.requirements = Requirements()
        # self.resources and self.start_time will most likely be set
        # by the scheduling algorithm
        self.start_time = start_time
        self.resources = resources

    def fits(self, resource):
        """Return true if the task matches the resource.

        Tests whether this task matches the resource passed to
        it.
        :param resource: a resource
        :type resource:
        """
        # TODO
        return True

    def encode(self):
        """Return the Task as a dictionary object.

        """
        result = dict(self.__dict__)
        if result['requirements'] is not None:
            result['requirements'] = result['requirements'].encode()
        return result

    @staticmethod
    def decode(data):
        """Construct a Task from a dictionary.

        """
        data = dict(data)
        # Decode any requirements data
        if data['requirements'] is not None:
            data['requirements'] = Requirements.decode(data['requirements'])
        return Task(**data)


class Requirements:
    """Requirements of a given Task.

    This class specifies all the base requirements for a particular Task.
    """

    # TODO: Add more requirement types
    def __init__(self, max_cores=1, min_cores=1):
        """"""
        self.max_cores = max_cores
        self.min_cores = min_cores

    def encode(self):
        """Encode Requirements into a JSON-serializable object.

        """
        return self.__dict__

    @staticmethod
    def decode(data):
        """Return a Requirements object from a basic Python dict.

        Produces a Requirements object from a Python dict.
        :param data: requirements data
        :type data: dict
        """
        return Requirements(**data)


# TODO: Add a generic way to add resource types to a ResourceCollection
class ResourceCollection:
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


class ResourceSubset:
    """Resource subset class.

    Generic class for holding a subset of a collection of resources,
    which may or may not include all of the resources of the parent
    ResourceCollection class with the same id_.
    """

    def __init__(self, id_, cores=1):
        """Resource collection constructor.

        Initialize a new ResourceCollection object with resource details.
        :param id_: id of the resource being utilized
        :type id_: str
        :param cores: number of cores used
        :type cores: int
        """
        self.id_ = id_
        self.cores = cores
