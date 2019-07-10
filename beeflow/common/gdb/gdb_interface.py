"""Mid-level graph database management interface."""

from beeflow.common.gdb.neo4j_driver import Neo4jDriver


class GraphDatabaseInterface:
    """Interface for managing a graph database with workflows.

    Delegates the actual work to an instance of a subclass of
    the abstract base class `GraphDatabaseDriver`. By default,
    this is the `Neo4jDriver` class.
    """

    @classmethod
    def connect(cls, gdb_driver=Neo4jDriver, **kwargs):
        """Initialize a graph database interface with a driver.

        :param gdb_driver: the graph database driver (Neo4jDriver by default)
        :type gdb_driver: subclass of GraphDatabaseDriver
        :param kwargs: optional arguments for the graph database driver
        """
        cls._gdb_driver = gdb_driver(**kwargs)

    @classmethod
    def load_workflow(cls, workflow):
        """Load a BEE workflow into the graph database.

        :param workflow: the new workflow to load
        :type workflow: instance of Workflow
        """
        cls._gdb_driver.load_workflow(workflow)

    @classmethod
    def get_subworkflow(cls, head_tasks):
        """Get sub-workflows from the graph database with the specified head tasks.

        :param head_tasks: the head tasks of the sub-workflows
        :type head_tasks:
        :rtype: instance of Workflow
        """

    @classmethod
    def initialize_workflow(cls):
        """Start the workflow loaded into the graph database."""
        cls._gdb_driver.initialize_workflow()

    @classmethod
    def get_dependent_tasks(cls, task):
        """Get the dependents of a task in a graph database workflow.

        :param task: the task whose dependents to obtain
        :type task: instance of Task
        :rtype: set of Task instances
        """
        return cls._gdb_driver.get_dependent_tasks(task)

    @classmethod
    def get_task_state(cls, task):
        """Get the state of a task in a graph database workflow.

        :param task: the task whose state to obtain
        :type task: instance of Task
        :rtype: string
        """
        return cls._gdb_driver.get_task_state(task)

    @classmethod
    def finalize_workflow(cls):
        """Finalize the BEE workflow loaded into the graph database."""
        cls._gdb_driver.finalize_workflow()
