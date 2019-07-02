"""Neo4j interface module."""

import neo4j

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "neo4j"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database."""

    def __init__(self, uri=DEFAULT_URI, user=DEFAULT_USER,
                 password=DEFAULT_PASSWORD):
        """Create a new Neo4j database driver.

        :param uri: the URI of the Neo4j database
        :type uri: string
        :param user: the username for the database user account
        :type user: string
        :param password: the password for the database user account
        :type password: string
        """
        self._driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))

    def load_workflow_dag(self, workflow):
        """Load the workflow as a DAG into the Neo4j database.

        :param workflow: the workflow to load as a DAG
        :type workflow: instance of Workflow
        """

    def initialize_workflow_dag(self):
        """Initialize the workflow loaded into the Neo4j database."""

    def start_ready_tasks(self):
        """Start tasks that have no unsatisfied dependencies."""

    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    def get_dependent_tasks(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """

    def get_task_status(self, task):
        """Get the status of a task in the Neo4j workflow DAG.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """

    def finalize_workflow_dag(self):
        """Finalize the workflow DAG loaded into the Neo4j database."""

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()
