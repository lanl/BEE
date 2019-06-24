"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database."""

    @abstractmethod
    def load_workflow(self, inputs, outputs):
        """Load the workflow as a DAG into the graph database."""

    @abstractmethod
    def initialize_workflow(self):
        """Initialize the workflow loaded into the graph database."""

    @abstractmethod
    def get_dependents(self, task):
        """Get the dependent tasks of a specified workflow task."""

    @abstractmethod
    def finalize_workflow(self):
        """Finalize the workflow loaded into the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
