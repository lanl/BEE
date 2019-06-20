"""Neo4j interface module."""

from neo4j import GraphDatabase

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "neo4j"


class Neo4jDriver:
    """The driver for a Neo4j Database."""

    def __init__(self, uri=DEFAULT_URI, user=DEFAULT_USER,
                 password=DEFAULT_PASSWORD):
        """Create a new Neo4j database driver.

        :param uri (str): The URI of the Neo4j database
        :param user (str): The username for the database user account
        :param password (str): The password for the database user account
        """
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def _close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()
