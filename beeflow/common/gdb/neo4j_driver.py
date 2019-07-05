"""Neo4j interface module."""

from string import Template

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

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
        try:
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
            self._workflows = []
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def load_workflow_dag(self, workflow):
        """Load the workflow as a DAG into the Neo4j database.

        :param workflow: the workflow to load as a DAG
        :type workflow: instance of Workflow
        """
        # Construct the Neo4j Cypher query
        cypher_query = (self._construct_create_statements(workflow.tasks)
                        + self._construct_merge_statements(workflow.tasks))

        # Commit the query transaction in a Neo4j session
        with self._driver.session() as session:
            session.run(cypher_query)

        self._workflows.append(workflow)

    def initialize_workflow_dags(self):
        """Initialize the workflow loaded into the Neo4j database."""
        READY_QUERY = ('MATCH (t) WHERE NOT (t:Task)-[:DEPENDS]->() '
                       'SET t.state = "READY"')

        with self._driver.session() as session:
            session.run(READY_QUERY)

    def start_ready_tasks(self):
        """Start tasks that have no unsatisfied dependencies."""
        START_QUERY = ('MATCH (t:Task {state: "READY"}) '
                       'SET t.state = "RUNNING"')

        with self._driver.session() as session:
            session.run(START_QUERY)

    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    def get_dependent_tasks(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """
        DEP_QUERY = ('MATCH (:Task {name: "$name"})<-[:DEPENDS]-(t:Task) '
                     'RETURN t')

        with self._driver.session() as session:
            deps = session.run(DEP_QUERY, name=task.name).single().value()

        return deps

    def get_task_state(self, task):
        """Get the status of a task in the Neo4j workflow DAG.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """
        STATUS_QUERY = 'MATCH (t:Task {name: "$name"}) RETURN t.state'

        with self._driver.session() as session:
            state = session.run(STATUS_QUERY, name=task.name).single().value()

        return state

    def finalize_workflow_dags(self):
        """Finalize the workflow DAG loaded into the Neo4j database."""

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        CLEANUP_QUERY = 'MATCH (n) DETACH DELETE n'

        with self._driver.session() as session:
            session.run(CLEANUP_QUERY)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    # Cypher statement construction helpers
    def _construct_create_statements(self, tasks):
        """Construct a series of CREATE statements for the tasks.

        :param tasks: the new tasks to add
        :type tasks: list of Task instances
        """
        CREATE_TEMP = Template(
                'CREATE ($task_id:Task {name:"$name", state:"WAITING"})')
        create_stmts = [CREATE_TEMP.substitute(task_id=task.id, name=task.name)
                        for task in tasks]
        return "\n".join(create_stmts) + "\n"

    def _construct_merge_statements(self, tasks):
        """Construct a series of MERGE statements for task dependencies.

        :param tasks: the tasks whose dependencies to add as relationships
        :type tasks: list of Task instances
        """
        DEP_TEMP = Template("MERGE ($dependent)-[:DEPENDS]->($dependency)")
        merge_stmts = [DEP_TEMP.substitute(dependent=task.id,
                                           dependency=dependency)
                       for task in tasks
                       for dependency in task.dependencies]
        return "\n".join(merge_stmts) + "\n"
