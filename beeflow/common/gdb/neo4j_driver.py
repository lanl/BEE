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
            self._set_tasks_unique()
        except ServiceUnavailable:
            print("Neo4j database unavailable. Is it running?")

    def load_workflow_dag(self, workflow):
        """Load the workflow as a DAG into the Neo4j database.

        :param workflow: the workflow to load as a DAG
        :type workflow: instance of Workflow
        """
        # Construct the Neo4j Cypher query
        cypher_query = (_construct_create_statements(workflow.tasks)
                        + _construct_merge_statements(workflow.tasks))

        # Commit the query transaction in a Neo4j session
        self._run_query(cypher_query)
        self._workflows.append(workflow)

    def initialize_workflow_dags(self):
        """Initialize the workflow DAGs loaded into the Neo4j database."""
        ready_query = 'MATCH (t) WHERE NOT (t:Task)-[:DEPENDS]->() SET t.state = "READY"'
        self._run_query(ready_query)

    def start_ready_tasks(self):
        """Start tasks that have no unsatisfied dependencies."""
        start_query = 'MATCH (t:Task {state: "READY"}) SET t.state = "RUNNING"'
        self._run_query(start_query)

    def watch_tasks(self):
        """Watch tasks for completion/failure and start new ready tasks."""

    def get_dependent_tasks(self, task):
        """Get the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task object
        :rtype: set of Task objects
        """
        dependents_query = 'MATCH (:Task {name: "$name"})<-[:DEPENDS]-(t:Task) RETURN t'
        deps = self._run_query(dependents_query, name=task.name).values()
        return deps

    def get_subworkflow(self, head_tasks):
        """Get sub-workflows from the Neo4j database with the specified head tasks.

        :param head_tasks: the head tasks of the sub-workflows
        :type head_tasks: list of Task instances
        :rtype: instance of Workflow
        """"

    def get_task_status(self, task):
        """Get the status of a task in the Neo4j workflow DAG.

        :param task: the task whose status to retrieve
        :type task: instance of Task
        :rtype: a string
        """
        status_query = 'MATCH (t:Task {name: "$name"}) RETURN t.state'
        return self._run_query(status_query, name=task.name).single().value()

    def finalize_workflow_dags(self):
        """Finalize the workflow DAGs loaded into the Neo4j database."""

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        cleanup_query = "MATCH(n) WITH n LIMIT 10000 DETACH DELETE n;"
        self._run_query(cleanup_query)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    def _set_tasks_unique(self):
        unique_query = "CREATE CONSTRAINT ON (t:Task) ASSERT t.name IS UNIQUE"
        self._run_query(unique_query)

    def _run_query(self, cypher_query, **kwargs):
        """Run a Neo4j query using Cypher.

        :param cypher_query: the query to run
        :type cypher_query: string
        :param kwargs: parameters for query variable substitution
        """
        with self._driver.session() as session:
            result = session.run(cypher_query, **kwargs)
        return result


# Cypher statement construction helpers
def _construct_create_statements(tasks):
    """Construct a series of CREATE statements for the tasks.

    :param tasks: the new tasks to add
    :type tasks: list of Task instances
    """
    create_template = Template('CREATE ($task_id:Task {name:"$name", state:"WAITING"})')
    create_stmts = [create_template.substitute(task_id=task.id, name=task.name)
                    for task in tasks]
    return "\n".join(create_stmts) + "\n"


def _construct_merge_statements(tasks):
    """Construct a series of MERGE statements for task dependencies.

    :param tasks: the tasks whose dependencies to add as relationships
    :type tasks: list of Task instances
    """
    dependency_template = Template("MERGE ($dependent)-[:DEPENDS]->($dependency)")
    merge_stmts = [dependency_template.substitute(dependent=task.id, dependency=dependency)
                   for task in tasks for dependency in task.dependencies]
    return "\n".join(merge_stmts) + "\n"
