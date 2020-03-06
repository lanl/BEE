"""Abstract base class for the handling of workflow DAGs."""

from abc import ABC, abstractmethod


class GraphDatabaseDriver(ABC):
    """Driver interface for a generic graph database.

    The driver must implement a __init__ method that creates/connects to
    the graph database and returns some kind of 'connection' object.
    """

    @abstractmethod
    def initialize_workflow(self, name, inputs, outputs, requirements, hints):
        """Begin construction of a workflow in the graph database.

        Create the bee_init (with inputs), bee_exit (with outputs) nodes, and metadata
        nodes and store the requirements and hints in the metadata node.

        :param name: a name for the workflow
        :type name: string
        :param inputs: the inputs to the workflow
        :type inputs: set of strings
        :param outputs: the outputs of the workflow
        :type outputs: set of strings
        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        """

    @abstractmethod
    def execute_workflow(self):
        """Begin execution of the stored workflow.

        Set the bee_init task's state to be ready.
        """

    @abstractmethod
    def load_task(self, task):
        """Load a task into the stored workflow.

        Dependencies are automatically deduced and generated by the graph database
        upon loading each task by matching task inputs and outputs.

        :param task: a workflow task
        :type task: instance of Task
        """

    @abstractmethod
    def get_task_by_id(self, task_id):
        """Return a workflow task record from the graph database.

        :param task_id: a task's ID
        :type task_id: instance of Task
        :rtype: a query result object
        """

    @abstractmethod
    def get_workflow_tasks(self):
        """Return a list of all workflow task records from the graph database.

        :rtype: a query result object
        """

    @abstractmethod
    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the graph database.

        Must return a tuple with the format (requirements, hints)

        :rtype: (set of Requirement, set of Requirement)
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
    def set_task_state(self, task, state):
        """Set the state of a task in the graph database workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        :param state: the new state
        :type state: string
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
