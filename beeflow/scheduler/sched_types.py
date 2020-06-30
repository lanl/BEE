"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""


class Task:
    """Representation of a Task and its various requirements.

    This class represents the class as a set of resource requirements
    which can be used by the scheduling algorithm to easily determine
    the best allocation.
    """

    def __init__(self, workflow_name, task_name, max_runtime):
        """Task constructor.

        Create a new Task with given parameters.
        :param workflow_name:
        :type workflow_name:
        :param task_name:
        :type task_name:
        :param max_runtime:
        :type max_runtime:
        """
        self.workflow_name = workflow_name
        self.task_name = task_name
        self.max_runtime = max_runtime

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
        return self.__dict__

    @staticmethod
    def decode(data):
        """Construct a Task from a dictionary.

        """
        return Task(**data)


class ResourceCollection:
    """Resource collection class.

    Generic class for holding a collection of resources.
    """

    def __init__(self, id_, cores=1):
        """Resource collection constructor.

        Initialize a new ResourceCollection object with resource details.
        """
        # TODO
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
        """
        # TODO
        self.id_ = id_
        self.cores = cores
