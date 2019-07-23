"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database.

    The driver must implement a __init__ method that creates/connects to
    the graph database.
    """

    @abstractmethod
    def load_workflow(self, workflow):
        """Load the workflow into the graph database.

        :param workflow: the workflow to load
        :type workflow: instance of Workflow
        """

    @abstractmethod
    def add_init_node(self):
        """Add a task node with the name 'bee_init' and state 'WAITING'."""

    @abstractmethod
    def add_exit_node(self):
        """Add a task node with the name 'bee_exit' and state 'WAITING'."""

    @abstractmethod
    def get_subworkflow_ids(self, subworkflow):
        """Return a subworkflow's task IDs from the graph database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: list of integers
        """

    @abstractmethod
    def initialize_workflow(self):
        """Initialize the workflow loaded into the graph database."""

    @abstractmethod
    def start_ready_tasks(self):
        """Start tasks in the loaded workflows that have no dependencies."""

    @abstractmethod
    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    @abstractmethod
    def get_head_task_names(self):
        """Return all tasks with no dependents."""

    @abstractmethod
    def get_tail_task_names(self):
        """Return all tasks with no dependencies."""

    @abstractmethod
    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a workflow task in the graph database.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: set of Task instances
        """

    @abstractmethod
    def get_task_state(self, task):
        """Return the state of a task in the workflow.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """

    @abstractmethod
    def finalize_workflow(self):
        """Finalize the workflow loaded into the graph database."""

    @abstractmethod
    def cleanup(self):
        """Clean up all the data stored in the graph database."""

    @abstractmethod
    def close(self):
        """Close the connection to the graph database."""
