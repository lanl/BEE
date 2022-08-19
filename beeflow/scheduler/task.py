"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""
from beeflow.scheduler import serializable
from beeflow.scheduler import resource_allocation


class Task(serializable.Serializable):
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
        self.requirements = (
            resource_allocation.Requirements.decode(requirements)
            if requirements is not None else {}
        )
        self.allocations = allocations if allocations is not None else []

    def encode(self):
        """Encode and return a simple Python data type.

        Produce a simple Python data type for serialization.
        """
        result = dict(self.__dict__)
        if 'allocations' in result and result['allocations']:
            result['allocations'] = [alloc.encode()
                                     for alloc in result['allocations']]
        if 'requirements' in result and result['requirements'] is not None:
            # result['requirements'] = result['requirements'].__dict__
            result['requirements'] = result['requirements'].encode()
        return result

    @staticmethod
    def decode(data):
        """Decode a serialized object and return an instance.

        Decode a simple Python data type and return and instance of
        the object.
        """
        data = dict(data)
        return Task(**data)
