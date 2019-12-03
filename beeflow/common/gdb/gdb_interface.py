"""Mid-level interface for managing a graph database with workflows.

Delegates the actual work to an instance of a subclass of
the abstract base class `GraphDatabaseDriver`. By default,
this is the `Neo4jDriver` class.
"""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver


class GraphDatabaseInterface:
    """Interface for managing a graph database with workflows.

    Requires an implemented subclass of GDBDriver to function.
    """

    def __init__(self, gdb_driver=Neo4jDriver):
        """Initialize the graph database interface with a graph database driver.

        :param gdb_driver: the graph database driver (Neo4jDriver by default)
        :type gdb_driver: subclass of GraphDatabaseDriver
        """
        # Store the GDB driver state
        self._gdb_driver = gdb_driver
        self._connection = None

    def __del__(self):
        """Deconstruct the GraphDatabaseInterface.

        Automatically disconnect from the graph database.
        """
        self.close()

    def connect(self, **kwargs):
        """Initialize a graph database interface with a driver.

        :param kwargs: arguments for initializing the graph database connection
        """
        # Initialize the graph database driver
        self._connection = self._gdb_driver(**kwargs)

    def load_workflow(self, workflow):
        """Load a BEE workflow into the graph database.

        :param workflow: the new workflow to load
        :type workflow: instance of Workflow
        """
        # Load the workflow into the graph database
        self._connection.load_workflow(workflow)

    def initialize_workflow(self):
        """Start the workflow loaded into the graph database."""
        self._connection.initialize_workflow()

    def finalize_workflow(self):
        """Finalize the workflow loaded into the graph database."""
        self._connection.finalize_workflow()

    def get_workflow_tasks(self):
        """Return a workflow's Task objects from the graph database."""
        task_records = self._connection.get_workflow_tasks()
        return [self._connection.reconstruct_task(task_record) for task_record in task_records]

    def get_workflow_requirements_and_hints(self):
        """Return a tuple containing a list of requirements and a list of hints.

        The returned tuple format is (requirements, hints).

        :rtype: (list of Requirement instances, list of Requirement instances)
        """
        requirements = self._connection.get_workflow_requirements()
        hints = self._connection.get_workflow_hints()
        return (requirements, hints)

    def get_subworkflow_tasks(self, subworkflow):
        """Return a subworkflow's Task objects from the graph database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: list of Task instances
        """
        task_records = self._connection.get_subworkflow_tasks(subworkflow)
        return [self._connection.reconstruct_task(task_record) for task_record in task_records]

    def get_dependent_tasks(self, task):
        """Return the dependents of a task in a graph database workflow.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: list of Task instances
        """
        task_records = self._connection.get_dependent_tasks(task)
        return [self._connection.reconstruct_task(task_record) for task_record in task_records]

    def get_task_state(self, task):
        """Return the state of a task in a graph database workflow.

        :param task: the task whose state to retrieve
        :type task: instance of Task
        :rtype: string
        """
        return self._connection.get_task_state(task)

    def set_task_state(self, task, state):
        """Set the state of a task in the graph database workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        :param state: the new state
        :type state: string
        """
        return self._connection.set_task_state(task, state)

    def empty(self):
        """Return true if the graph database is empty, else false.

        :rtype: boolean
        """
        return self._connection.empty()

    def cleanup(self):
        """Clean up all data in the graph database."""
        self._connection.cleanup()

    def close(self):
        """Close the connection to the graph database."""
        self._connection.close()
