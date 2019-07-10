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

    def load_workflow(self, workflow):
        """Load a BEE workflow into the graph database.

        :param workflow: the new workflow to load
        :type workflow: instance of Workflow
        """
        self._gdb_driver.load_workflow(workflow)

    def initialize_workflows(self):
        """Start the workflow loaded into the graph database."""
        self._gdb_driver.initialize_workflows()

    def get_dependent_tasks(self, task):
        """Get the dependents of a task in a graph database workflow.

        :param task: the task whose dependents to obtain
        :type task: instance of Task
        :rtype: set of Task instances
        """
        return self._gdb_driver.get_dependent_tasks(task)

    def get_subworkflow(self, head_tasks):
        """Get sub-workflows from the graph database with the specified head tasks.

        :param head_tasks: the head tasks of the sub-workflows
        :type head_tasks:
        :rtype: instance of Workflow
        """

    def finalize_workflows(self):
        """Finalize the BEE workflow loaded into the graph database."""
        self._gdb_driver.finalize_workflows()
