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

    def load_workflow(self, inputs, outputs):
        """Load the workflow as a DAG into the Neo4j database.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """

    def initialize_workflow(self):
        """Initialize the workflow loaded into the Neo4j database."""

    def get_dependents(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """

    def finalize_workflow(self):
        """Finalize the workflow loaded into the Neo4j database."""

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()
