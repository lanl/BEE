"""Mid-level graph database management interface."""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver


class GraphDatabaseInterface:
    """Interface for managing a graph database with workflows.

    Delegates the actual work to an instance of a subclass of
    the abstract base class `GraphDatabaseDriver`. By default,
    this is the `Neo4jDriver` class.
    """

    def __init__(self, gdb_driver=Neo4jDriver, **kwargs):
        """Initialize a graph database interface with a driver.

        :param gdb_driver: the graph database driver (Neo4jDriver by default)
        :type gdb_driver: subclass of GraphDatabaseDriver
        :param kwargs: optional arguments for the graph database driver
        """
        self._gdb_driver = gdb_driver(**kwargs)

    def load_workflow(self, inputs, outputs):
        """Load a BEE workflow into the graph database.

        :param inputs: The workflow inputs
        :type inputs: TBD
        :param outputs: The workflow outputs
        :type outputs: TBD
        """
        self._gdb_driver.load_workflow_dag(inputs, outputs)

    def initialize_workflow(self):
        """Initialize the BEE workflow loaded into the graph database."""
        self._gdb_driver.initialize_workflow_dag()

    def get_dependents(self, task):
        """Get the dependents of a task in the graph database workflow.

        :param task: the task whose dependents to obtain
        :type task: instance of Task
        :rtype: set of Task instances
        """
        return self._gdb_driver.get_dependents(task)

    def finalize_workflow(self):
        """Finalize the BEE workflow loaded into the graph database."""
        self._gdb_driver.finalize_workflow_dag()
