"""Neo4j interface module.

Connection requires a valid URI, Username, and Password.
The current defaults are defined below, but should later be
either standardized or read from a config file.
"""

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver
from beeflow.common.gdb import neo4j_cypher as tx
from beeflow.common.wf_data import Task, Requirement

# Default Neo4j authentication
# We may want to instead get these from a config at some point
DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "password"


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database.

    Implements GraphDatabaseDriver.
    Wraps the neo4j package proprietary driver.
    """

    def __init__(self, user=DEFAULT_USER, password=DEFAULT_PASSWORD, **kwargs):
        """Create a new Neo4j database driver.

        :param uri: the URI of the Neo4j database
        :type uri: string
        :param user: the username for the database user account
        :type user: string
        :param password: the password for the database user account
        :type password: string
        """

        bolt_port = kwargs.get('bolt_port',7687)
        db_hostname = kwargs.get('db_hostname','localhost')
        password = kwargs.get('dbpass','password')
        uri = 'bolt://'+db_hostname+':'+bolt_port

        try:
            # Connect to the Neo4j database using the Neo4j proprietary driver
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
            # Require tasks to have unique names
            self._require_tasks_unique()
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def load_task(self, task):
        """Load a task into the workflow stored in the Neo4j database.

        Dependencies are automatically deduced and generated by Neo4j upon loading
        each task by matching task inputs and outputs.

        :param task: a workflow task
        :type task: instance of Task
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_task, task=task)
            session.write_transaction(tx.add_dependencies, task=task)

    def initialize_workflow(self, inputs, outputs, requirements, hints):
        """Begin construction of a workflow stored in Neo4j.

        Creates the bee_init node with its inputs.
        Creates the bee_exit node with its outputs.
        Creates the metadata node with requirements and hints.

        :param inputs: the inputs to the workflow
        :type inputs: set of strings
        :param outputs: the outputs of the workflow
        :type outputs: set of strings
        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_bee_init_node, inputs=list(inputs))
            session.write_transaction(tx.create_bee_exit_node, outputs=list(outputs))
            session.write_transaction(tx.create_metadata_node, requirements=requirements,
                                      hints=hints)

    def execute_workflow(self):
        """Begin execution of the workflow stored in the Neo4j database."""
        self._write_transaction(tx.set_init_task_to_ready)

    def finalize_workflow(self):
        """Finalize the workflow stored in the Neo4j database.

        Sets the bee_exit node's state to READY.
        """
        self._write_transaction(tx.set_exit_task_to_ready)

    def get_task_by_id(self, task_id):
        """Return a workflow task record from the Neo4j database.

        :param task_id: a task's ID
        :type task_id: instance of Task
        :rtype: a query result object
        """
        return self._read_transaction(tx.get_task_by_id, task_id=task_id)

    def get_workflow_tasks(self):
        """Return all workflow task records from the Neo4j database.

        :rtype: BoltStatementResult
        """
        return self._read_transaction(tx.get_workflow_tasks)

    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the Neo4j database.

        Returns a tuple of (requirements, hints)

        :rtype: (set of Requirement, set of Requirement)
        """
        with self._driver.session() as session:
            requirements = _reconstruct_requirements(
                session.read_transaction(tx.get_workflow_requirements))
            hints = _reconstruct_requirements(
                session.read_transaction(tx.get_workflow_hints))
        return (requirements, hints)

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

    def set_task_state(self, task, state):
        """Set the state of a task in the Neo4j workflow.

        :param task: the task whose state to change
        :type task: instance of Task
        :param state: the new state
        :type state: string
        """
        self._write_transaction(tx.set_task_state, task=task, state=state)

    def reconstruct_task(self, task_record):
        """Reconstruct a Task object by its record retrieved from Neo4j.

        :param task_record: the database record of the task
        :rtype: instance of Task
        """
        rec = task_record["t"]
        t = Task(name=rec["name"], command=rec["command"],
                 hints=_reconstruct_requirements(rec["hints"]),
                 subworkflow=rec["subworkflow"], inputs=set(rec["inputs"]),
                 outputs=set(rec["outputs"]))
        # This is a bit of a hack for now. No method on Task to set task id.
        t.id = rec["task_id"]
        return t

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

    def _create_metadata_node(self, requirements, hints):
        """Create a graph node to contain workflow metadata.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints
        :type hints: set of Requirement instances
        """
        self._write_transaction(tx.create_metadata_node, requirements=requirements, hints=hints)

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
            session.write_transaction(tx_fun, **kwargs)


def _reconstruct_requirements(list_repr):
    """Reconstruct a task requirement from its list encoding.

    The list representation must conform to the following pattern:
    [class1, key1, value1, class2, key2, value2, ...].

    :param list_repr: the list representation of the dictionary
    :type list_repr: list of strings
    :rtype: set of Requirement instances
    """
    if list_repr is None:
        return set()

    def _str_is_integer(str_):
        """Test if a string can be represented as an integer.

        :param str_: the string to test
        :type str_: string
        """
        return str.isdigit(str_)

    def _str_is_float(str_):
        """Test if a string can be represented as a float.

        :param str_: the string to test
        :type str_: string
        """
        try:
            float(str_)
        except ValueError:
            return False
        else:
            return True

    # Convert string to original value if applicable
    # Grab 3-tuples from list-of-string representation of requirements
    # Return a set of requirements
    reqs = set()
    for (req_class, key, val) in zip(list_repr[:-2:3], list_repr[1:-1:3], list_repr[2::3]):
        if _str_is_integer(val):
            val = int(val)
        elif _str_is_float(val):
            val = float(val)
        elif val == "True":
            val = True
        elif val == "False":
            val = False

        reqs.add(Requirement(req_class, key, val))

    return reqs