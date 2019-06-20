"""Interface for the handling of workflow DAGs."""

from beeflow.common.gdb.bee_neo4j import Neo4jDriver


class GraphDatabase:
    """Driver interface for a generic graph database."""

    def __init__(self, driver=Neo4jDriver, **kwargs):
        """Create a new Graph Database driver."""
        self._driver = driver(**kwargs)

    def load_workflow_dag(self, inputs, outputs):
        """Load the workflow as a DAG into the graph database."""

    def initialize_workflow_dag(self):
        """Initialize the workflow loaded into the graph database."""

    def get_dependents_dag(self, task):
        """Get the dependent tasks of a specified task."""

    def finalize_workflow_dag(self):
        """Finalize the workflow loaded into the graph database."""
