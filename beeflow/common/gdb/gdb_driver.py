"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database."""

    @abstractmethod
    def load_workflow(self, workflow):
        """Load the workflow as a DAG into the graph database.

        :param workflow: the workflow to load
        :type workflow: instance of Workflow
        """

    @abstractmethod
    def get_subworkflow(self, head_tasks):
        """Get sub-workflows from the graph database with the specified head tasks.

        :param head_tasks: the head tasks of the sub-workflows
        :type head_tasks: list of Task instances
        :rtype: instance of Workflow
        """

    @abstractmethod
    def initialize_workflows(self):
        """Initialize the workflow DAGs loaded into the graph database."""

    @abstractmethod
    def start_ready_tasks(self):
        """Start tasks in the loaded workflows that have no dependencies."""

    @abstractmethod
    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    @abstractmethod
    def get_dependent_tasks(self, task):
        """Get the dependent tasks of a workflow task in the graph database.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: set of Task instances
        """

    @abstractmethod
    def get_task_state(self, task):
        """Get the state of a task in the workflow DAG.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """

    @abstractmethod
    def finalize_workflows(self):
        """Finalize the workflow DAGs loaded into the graph database."""

    @abstractmethod
    def cleanup(self):
        """Clean up all the data stored in the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
