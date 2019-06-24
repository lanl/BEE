"""Neo4j interface module."""

import neo4j

from beeflow.common.gdb.bee_gdb import GraphDatabaseDriver

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "neo4j"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database."""

    def __init__(self, uri=DEFAULT_URI, user=DEFAULT_USER,
                 password=DEFAULT_PASSWORD):
        """Create a new Neo4j database driver.

        :param uri (str): The URI of the Neo4j database
        :param user (str): The username for the database user account
        :param password (str): The password for the database user account
        """
        self._driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))

    def load_workflow(self, inputs, outputs):
        """Load the workflow as a DAG into the Neo4j database."""

    def initialize_workflow(self):
        """Initialize the workflow loaded into the Neo4j database."""

    def get_dependents(self, task):
        """Get the dependent tasks of a specified workflow task."""

    def finalize_workflow(self):
        """Finalize the workflow loaded into the Neo4j database."""

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()
