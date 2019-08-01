"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database.

    The driver must implement a __init__ method that creates/connects to
    the graph database and returns some kind of 'connection' object.
    """

    @abstractmethod
    def load_workflow(self, workflow):
        """Load the workflow into the graph database.

        :param workflow: the workflow to load
        :type workflow: instance of Workflow
        """

    @abstractmethod
    def initialize_workflow(self):
        """Initialize the workflow loaded into the graph database.

        Sets the bee_init node's state to ready.
        """

    @abstractmethod
    def finalize_workflow(self):
        """Finalize the workflow loaded into the graph database.

        Sets the bee_exit node's state to READY.
        """

    @abstractmethod
    def get_workflow_tasks(self):
        """Return a list of all workflow task records from the graph database.

        :rtype: a query result object
        """

    @abstractmethod
    def get_subworkflow_tasks(self, subworkflow):
        """Return a list of subworkflow task records from the graph database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: a query result object
        """

    @abstractmethod
    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a workflow task in the graph database.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: set of Task instances
        """

    @abstractmethod
    def get_task_state(self, task):
        """Return the state of a task in the graph database workflow.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """

    @abstractmethod
    def set_task_state(self, task):
        """Set the state of a task in the graph database workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        """

    @abstractmethod
    def reconstruct_task(self, task_record):
        """Reconstruct a Task object by its record retrieved from the database.

        :param task_record: the database record of the task
        :rtype: instance of Task
        """

    @abstractmethod
    def empty(self):
        """Determine if the database is empty.

        :rtype: boolean
        """

    @abstractmethod
    def cleanup(self):
        """Clean up all the data stored in the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
