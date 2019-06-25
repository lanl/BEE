"""High-level workflow management interface."""

from beeflow.common.gdb.bee_neo4j import Neo4jDriver


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabaseDriver subclass.
    By default, this is the Neo4jDriver class.
    """

    def __init__(self, inputs, outputs, gdb_driver=Neo4jDriver, **kwargs):
        """Initialize the BEE workflow interface.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        :param gdb_driver: the graph database driver to use
        :type gdb_driver: implementing subclass of GraphDatabaseDriver
        :param kwargs: optional arguments for the driver
        """
        self._gdb_driver = gdb_driver(**kwargs)
        self.load_workflow(inputs, outputs)

    def load_workflow(self, inputs, outputs):
        """Load a new BEE workflow.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self._gdb_driver.load_workflow(inputs, outputs)

    def initialize_workflow(self):
        """Initialize the workflow."""
        self._gdb_driver.initialize_workflow()

    def get_dependents(self, task):
        """Get the dependent tasks of a specified task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """
        self._gdb_driver.get_dependents(task)

    def finalize_workflow(self):
        """Finalize the workflow."""
        self._gdb_driver.finalize_workflow()
