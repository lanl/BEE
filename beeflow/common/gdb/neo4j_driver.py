"""Neo4j interface module."""

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver
import beeflow.common.gdb.neo4j_cypher as tx

DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "neo4j"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database."""

    def __init__(self, uri=DEFAULT_URI, user=DEFAULT_USER, password=DEFAULT_PASSWORD):
        """Create a new Neo4j database driver.

        :param uri: the URI of the Neo4j database
        :type uri: string
        :param user: the username for the database user account
        :type user: string
        :param password: the password for the database user account
        :type password: string
        """
        try:
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
            self._require_tasks_unique()
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def load_workflow(self, workflow):
        """Load the workflow as a DAG into the Neo4j database.

        :param workflow: the workflow to load as a DAG
        :type workflow: instance of Workflow
        """
        for task in workflow.tasks:
            # The create_task transaction function returns the new task's Neo4j ID
            self._write_transaction(tx.create_task, task=task)

        for task in workflow.tasks:
            self._write_transaction(tx.add_dependencies, task=task)

    def get_subworkflow(self, head_tasks):
        """Get sub-workflows from the Neo4j database with the specified head tasks.

        :param head_tasks: the head tasks of the sub-workflows
        :type head_tasks: list of Task instances
        :rtype: instance of Workflow
        """

    def initialize_workflow(self):
        """Initialize the workflow DAGs loaded into the Neo4j database."""
        self._write_transaction(tx.set_head_tasks_to_ready)

    def start_ready_tasks(self):
        """Start tasks that have no unsatisfied dependencies."""
        self._write_transaction(tx.set_ready_tasks_to_running)

    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    def get_dependent_tasks(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """
        return self._read_transaction(tx.get_dependent_tasks, task=task)

    def get_task_state(self, task):
        """Get the state of a task in the Neo4j workflow DAG.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """
        return self._read_transaction(tx.get_task_state, task=task)

    def finalize_workflow(self):
        """Finalize the workflow DAGs loaded into the Neo4j database."""

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        self._write_transaction(tx.cleanup)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    def _require_tasks_unique(self):
        """Require tasks to have unique names."""
        self._write_transaction(tx.constrain_tasks_unique)

    def _read_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j read transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        with self._driver.session() as session:
            result = session.read_transaction(tx_fun, **kwargs)
        return result

    def _write_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j write transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        with self._driver.session() as session:
            result = session.write_transaction(tx_fun, **kwargs)
        return result
