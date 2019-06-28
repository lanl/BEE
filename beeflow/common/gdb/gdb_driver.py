"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database."""

    @abstractmethod
    def load_workflow_dag(self, inputs, outputs):
        """Load the workflow as a DAG into the graph database.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """

    @abstractmethod
    def initialize_workflow_dag(self):
        """Initialize the workflow loaded into the graph database."""

    @abstractmethod
    def get_dependents(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """

    @abstractmethod
    def finalize_workflow_dag(self):
        """Finalize the workflow loaded into the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
