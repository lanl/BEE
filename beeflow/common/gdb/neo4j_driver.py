"""Neo4j interface module."""

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver
from beeflow.common.gdb import neo4j_cypher as tx
from beeflow.common.data.wf_data import Task

# Default Neo4j authentication
# We may want to instead get these from a config at some point
DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "neo4j"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database.

    Implements GraphDatabaseDriver.
    """

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
            # Connect to the Neo4j database using the Neo4j proprietary driver
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
            # Require tasks to have unique names
            self._require_tasks_unique()
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def load_workflow(self, workflow):
        """Load the workflow into the Neo4j database.

        :param workflow: the workflow to load
        :type workflow: instance of Workflow
        """
        # Load tasks as nodes in the database
        for task in workflow.tasks:
            # The create_task transaction function returns the new task's Neo4j ID
            self._write_transaction(tx.create_task, task=task)

        # Load the dependencies as relationships in the database
        for task in workflow.tasks:
            self._write_transaction(tx.add_dependencies, task=task)

    def initialize_workflow(self):
        """Initialize the workflow loaded into the Neo4j database.

        Sets the bee_init node's state to ready.
        """
        self._write_transaction(tx.set_init_task_to_ready)

    def finalize_workflow(self):
        """Finalize the workflow loaded into the Neo4j database.

        Sets the bee_exit node's state to READY.
        """
        self._write_transaction(tx.set_exit_task_to_ready)

    def get_workflow_tasks(self):
        """Return all workflow task records from the Neo4j database.

        :rtype: BoltStatementResult
        """
        return self._read_transaction(tx.get_workflow_tasks)

    def get_subworkflow_tasks(self, subworkflow):
        """Return task records from the Neo4j database.

        :param subworkflow: the unique identifier of the subworkflow
        :type subworkflow: string
        :rtype: BoltStatementResult
        """
        return self._read_transaction(tx.get_subworkflow_tasks, subworkflow=subworkflow)

    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """
        return self._read_transaction(tx.get_dependent_tasks, task=task)

    def get_task_state(self, task):
        """Return the state of a task in the Neo4j workflow.

        :param task: the task whose state to retrieve
        :type task: instance of Task
        :rtype: a string
        """
        return self._read_transaction(tx.get_task_state, task=task)

    def set_task_state(self, task):
        """Set the state of a task in the Neo4j workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        """
        self._write_transaction(tx.set_task_state, task=task)

    def reconstruct_task(self, task_record):
        """Reconstruct a Task object by its record retrieved from Neo4j.

        :param task_record: the database record of the task
        :rtype: instance of Task
        """
        rec = task_record["t"]
        return Task(task_id=rec["task_id"], name=rec["name"],
                    command=rec["command"],
                    requirements=_reconstruct_dict(rec["requirements"]),
                    hints=_reconstruct_dict(rec["hints"]),
                    subworkflow=rec["subworkflow"], inputs=set(rec["inputs"]),
                    outputs=set(rec["outputs"]))

    def empty(self):
        """Determine if the database is empty.

        :rtype: boolean
        """
        return bool(self._read_transaction(tx.is_empty) is None)

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        self._write_transaction(tx.cleanup)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    def _require_tasks_unique(self):
        """Require tasks to have unique names."""
        self._write_transaction(tx.constrain_task_names_unique)

    def _read_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j read transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        # Wrapper for neo4j.Session.read_transaction
        with self._driver.session() as session:
            result = session.read_transaction(tx_fun, **kwargs)
        return result

    def _write_transaction(self, tx_fun, **kwargs):
        """Run a Neo4j write transaction.

        :param tx_fun: the transaction function to run
        :type tx_fun: function
        :param kwargs: optional parameters for the transaction function
        """
        # Wrapper for neo4j.Session.write_transaction
        with self._driver.session() as session:
            result = session.write_transaction(tx_fun, **kwargs)
        return result


def _reconstruct_dict(list_repr):
    """Reconstruct a dictionary from its list encoding.

    The list representation must conform to the following pattern:
    [k1, v1, k2, v2, ...].
    :param list_repr: the list representation of the dictionary
    :type list_repr: list of strings
    :rtype: dictionary
    """
    dict_ = {}
    for key, val in zip(list_repr[:-1:2], list_repr[1::2]):
        if val.isdigit():
            dict_[key] = int(val)
        else:
            dict_[key] = val
    return dict_
