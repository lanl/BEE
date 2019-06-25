"""High-level workflow management interface."""

from beeflow.common.gdb.bee_neo4j import Neo4jDriver


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabase class.
    """

        self._gdb = GraphDatabase()
    def __init__(self, inputs, outputs, gdb_driver=Neo4jDriver, **kwargs):
        """Initialize the BEE workflow interface.

        :param inputs (TBD): workflow inputs
        :param outputs (TBD): workflow outputs
        :param gdb_driver (GraphDatabaseDriver): A graph database
        driver that implements each of the abstract methods of the
        GraphDatabaseDriver abstract base class
        :param kwargs: additional arguments for the driver
        """
        self._gdb_driver = gdb_driver(**kwargs)
        self.load_workflow(inputs, outputs)

    def load_workflow(self, inputs, outputs):
        """Load a new BEE workflow.

        :param inputs (list): Workflow inputs
        :param outputs (list): Workflow outputs
        """
        self._gdb_driver.load_workflow(inputs, outputs)

    def initialize_workflow(self):
        """Initialize the workflow."""
        self._gdb_driver.initialize_workflow()

    def get_dependents(self, task):
        """Get the dependent tasks of a specified task.

        :param task (Task): The task whose dependents to get
        """
        self._gdb_driver.get_dependents(task)

    def finalize_workflow(self):
        """Finish the workflow."""
        self._gdb_driver.finalize_workflow()
