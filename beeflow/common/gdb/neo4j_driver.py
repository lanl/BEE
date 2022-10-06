"""Neo4j interface module.

Connection requires a valid URI, Username, and Password.
The current defaults are defined below, but should later be
either standardized or read from a config file.
"""

from neo4j import GraphDatabase as Neo4jDatabase
from neobolt.exceptions import ServiceUnavailable

from beeflow.common.gdb.gdb_driver import GraphDatabaseDriver
from beeflow.common.gdb import neo4j_cypher as tx
from beeflow.common.wf_data import (Workflow, Task, Requirement, Hint,
                                    InputParameter, OutputParameter, StepInput, StepOutput)

# Default Neo4j authentication
# We may want to instead get these from a config at some point
DEFAULT_HOSTNAME = "localhost"
DEFAULT_BOLT_PORT = "7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "password"


class Neo4JNotRunning(Exception):
    """Exception thrown when connection attempted while Neo4j is not running."""


class Neo4jDriver(GraphDatabaseDriver):
    """The driver for a Neo4j Database.

    Implements GraphDatabaseDriver.
    Wraps the neo4j package proprietary driver.
    """

    def __init__(self, user=DEFAULT_USER, password=DEFAULT_PASSWORD, **kwargs):
        """Create a new Neo4j database driver.

        :param uri: the URI of the Neo4j database
        :type uri: str
        :param user: the username for the database user account
        :type user: str
        :param password: the password for the database user account
        :type password: str
        """
        db_hostname = kwargs.get("db_hostname", DEFAULT_HOSTNAME)
        bolt_port = kwargs.get("bolt_port", DEFAULT_BOLT_PORT)
        password = kwargs.get("db_pass", DEFAULT_PASSWORD)
        uri = f"bolt://{db_hostname}:{bolt_port}"

        try:
            # Connect to the Neo4j database using the Neo4j proprietary driver
            self._driver = Neo4jDatabase.driver(uri, auth=(user, password))
        except ServiceUnavailable as sue:
            raise Neo4JNotRunning("Neo4j database is unavailable") from sue

    def initialize_workflow(self, workflow):
        """Begin construction of a workflow stored in Neo4j.

        Creates the Workflow, Requirement, and Hint nodes in the Neo4j database.

        :param workflow: the workflow description
        :type workflow: Workflow
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_workflow_node, workflow)
            session.write_transaction(tx.create_workflow_requirement_nodes,
                                      requirements=workflow.requirements)
            session.write_transaction(tx.create_workflow_hint_nodes, hints=workflow.hints)
            session.write_transaction(tx.create_workflow_input_nodes, inputs=workflow.inputs)
            session.write_transaction(tx.create_workflow_output_nodes, outputs=workflow.outputs)

    def execute_workflow(self):
        """Begin execution of the workflow stored in the Neo4j database."""
        self._write_transaction(tx.set_init_task_inputs)
        self._write_transaction(tx.set_init_tasks_to_ready)
        self._write_transaction(tx.set_workflow_state, state='RUNNING')

    def pause_workflow(self):
        """Pause execution of a running workflow in Neo4j.

        Sets tasks with state 'RUNNING' to 'PAUSED'.
        """
        with self._driver.session() as session:
            session.write_transaction(tx.set_workflow_state, state='PAUSED')

    def resume_workflow(self):
        """Resume execution of a paused workflow in Neo4j.

        Sets workflow state to 'PAUSED'
        """
        with self._driver.session() as session:
            session.write_transaction(tx.set_workflow_state, state='RESUME')

    def reset_workflow(self, new_id):
        """Reset the execution state of an entire workflow.

        Sets all task states to 'WAITING'.
        Changes the workflow ID of the Workflow and Task nodes with new_id.

        :param new_id: the new workflow ID
        :type new_id: str
        """
        with self._driver.session() as session:
            session.write_transaction(tx.reset_tasks_metadata)
            session.write_transaction(tx.reset_workflow_id, new_id=new_id)

    def load_task(self, task):
        """Load a task into a workflow stored in the Neo4j database.

        Dependencies are automatically deduced and generated by Neo4j upon loading
        each task by matching task inputs and outputs.

        Task hint nodes and metadata nodes are created for querying convenience.

        :param task: a workflow task
        :type task: Task
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_task, task=task)
            session.write_transaction(tx.create_task_hint_nodes, task=task)
            session.write_transaction(tx.create_task_requirement_nodes, task=task)
            session.write_transaction(tx.create_task_input_nodes, task=task)
            session.write_transaction(tx.create_task_output_nodes, task=task)
            session.write_transaction(tx.create_task_metadata_node, task=task)
            session.write_transaction(tx.add_dependencies, task=task)

    def initialize_ready_tasks(self):
        """Set runnable tasks to state 'READY'.

        Runnable tasks are tasks with all input dependencies fulfilled.
        """
        self._write_transaction(tx.set_runnable_tasks_to_ready)

    def restart_task(self, old_task, new_task):
        """Restart a failed task.

        Create a Task node for new_task with 'RESTARTED_FROM' relationship to the
        Task node of old_task.

        :param old_task: the failed task
        :type old_task: Task
        :param new_task: the new (restarted) task
        :type new_task: Task
        """
        with self._driver.session() as session:
            session.write_transaction(tx.create_task, task=new_task)
            session.write_transaction(tx.create_task_hint_nodes, task=new_task)
            session.write_transaction(tx.create_task_requirement_nodes, task=new_task)
            session.write_transaction(tx.create_task_input_nodes, task=new_task)
            session.write_transaction(tx.create_task_output_nodes, task=new_task)
            session.write_transaction(tx.create_task_metadata_node, task=new_task)
            session.write_transaction(tx.add_dependencies, task=new_task, old_task=old_task,
                                      restarted_task=True)

    def finalize_task(self, task):
        """Set task state to 'COMPLETED' and set inputs from source.

        :param task: the task to finalize
        :type task: Task
        """
        self._write_transaction(tx.set_task_state, task=task, state="COMPLETED")
        self._write_transaction(tx.copy_task_outputs, task=task)

    def get_task_by_id(self, task_id):
        """Return a reconstructed task from the Neo4j database.

        :param task_id: a task's ID
        :type task_id: str
        :rtype: Task
        """
        task_record = self._read_transaction(tx.get_task_by_id, task_id=task_id)
        tuples = self._get_task_data_tuples([task_record])
        return _reconstruct_task(tuples[0][0], tuples[0][1], tuples[0][2], tuples[0][3],
                                 tuples[0][4])

    def get_workflow_description(self):
        """Return a reconstructed Workflow object from the Neo4j database.

        :rtype: Workflow
        """
        workflow_record = self._read_transaction(tx.get_workflow_description)
        requirements, hints = self.get_workflow_requirements_and_hints()
        inputs, outputs = self.get_workflow_inputs_and_outputs()
        return _reconstruct_workflow(workflow_record, hints, requirements, inputs, outputs)

    def get_workflow_state(self):
        """Return the current workflow state from the Neo4j database.

        :rtype: str
        """
        return self._read_transaction(tx.get_workflow_state)

    def set_workflow_state(self, state):
        """Set the state of the workflow in the Neo4j database.

        :param state: the new state of the workflow
        :type state: str
        """
        self._write_transaction(tx.set_workflow_state, state=state)

    def get_workflow_tasks(self):
        """Return all workflow task records from the Neo4j database.

        :rtype: list of Task
        """
        task_records = self._read_transaction(tx.get_workflow_tasks)
        tuples = self._get_task_data_tuples(task_records)
        return [_reconstruct_task(tup[0], tup[1], tup[2], tup[3], tup[4]) for tup in tuples]

    def get_workflow_requirements_and_hints(self):
        """Return all workflow requirements and hints from the Neo4j database.

        Returns a tuple of (requirements, hints).

        :rtype: (list of Requirement, list of Hint)
        """
        with self._driver.session() as session:
            requirements = _reconstruct_requirements(
                session.read_transaction(tx.get_workflow_requirements))
            hints = _reconstruct_hints(session.read_transaction(tx.get_workflow_hints))
        return requirements, hints

    def get_workflow_inputs_and_outputs(self):
        """Return all workflow inputs and outputs from the Neo4j database.

        Returns a tuple of (inputs, outputs).

        :rtype: (list of InputParameter, list of OutputParameter)
        """
        with self._driver.session() as session:
            inputs = _reconstruct_workflow_inputs(session.read_transaction(tx.get_workflow_inputs))
            outputs = _reconstruct_workflow_outputs(
                session.read_transaction(tx.get_workflow_outputs))

        return inputs, outputs

    def get_ready_tasks(self):
        """Return tasks with state 'READY' from the graph database.

        :rtype: list of Task
        """
        task_records = self._read_transaction(tx.get_ready_tasks)
        tuples = self._get_task_data_tuples(task_records)
        return [_reconstruct_task(tup[0], tup[1], tup[2], tup[3], tup[4]) for tup in tuples]

    def get_dependent_tasks(self, task):
        """Return the dependent tasks of a specified workflow task.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: list of Task
        """
        task_records = self._read_transaction(tx.get_dependent_tasks, task=task)
        tuples = self._get_task_data_tuples(task_records)
        return [_reconstruct_task(tup[0], tup[1], tup[2], tup[3], tup[4]) for tup in tuples]

    def get_task_state(self, task):
        """Return the state of a task in the Neo4j workflow.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._read_transaction(tx.get_task_state, task=task)

    def set_task_state(self, task, state):
        """Set the state of a task in the Neo4j workflow.

        :param task: the task whose state to change
        :type task: Task
        :param state: the new state
        :type state: str
        """
        self._write_transaction(tx.set_task_state, task=task, state=state)

    def get_task_metadata(self, task):
        """Return the metadata of a task in the Neo4j workflow.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :rtype: dict
        """
        metadata_record = self._read_transaction(tx.get_task_metadata, task=task)
        return _reconstruct_metadata(metadata_record)

    def set_task_metadata(self, task, metadata):
        """Set the metadata of a task in the Neo4j workflow.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._write_transaction(tx.set_task_metadata, task=task, metadata=metadata)

    def get_task_input(self, task, input_id):
        """Get a task input object.

        :param task: the task whose input to retrieve
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :rtype: StepInput
        """
        input_record = self._read_transaction(tx.get_task_input, task=task, input_id=input_id)
        return _reconstruct_task_input(input_record["i"])

    def set_task_input(self, task, input_id, value):
        """Set the value of a task input.

        :param task: the task whose input to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param value: str or int or float
        """
        self._write_transaction(tx.set_task_input, task=task, input_id=input_id, value=value)

    def get_task_output(self, task, output_id):
        """Get a task output object.

        :param task: the task whose output to retrieve
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :rtype: StepOutput
        """
        output_record = self._read_transaction(tx.get_task_output, task=task, output_id=output_id)
        return _reconstruct_task_output(output_record["o"])

    def set_task_output(self, task, output_id, value):
        """Set the value of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param value: the output value to set
        :type value: str or int or float
        """
        self._write_transaction(tx.set_task_output, task=task, output_id=output_id, value=value)

    def set_task_input_type(self, task, input_id, type_):
        """Set the type of a task input.

        :param task: the task whose input type to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param type_: the input type to set
        :param type_: str
        """
        self._write_transaction(tx.set_task_input_type, task=task, input_id=input_id, type_=type_)

    def set_task_output_glob(self, task, output_id, glob):
        """Set the glob of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param glob: the output glob to set
        :type glob: str
        """
        self._write_transaction(tx.set_task_output_glob, task=task, output_id=output_id, glob=glob)

    def workflow_completed(self):
        """Determine if a workflow in the Neo4j database has completed.

        A workflow has completed if each of its final task nodes have state 'COMPLETED'.
        :rtype: bool
        """
        return self._read_transaction(tx.final_tasks_completed)

    def empty(self):
        """Determine if the Neo4j database is empty.

        :rtype: bool
        """
        return self._read_transaction(tx.is_empty)

    def cleanup(self):
        """Clean up all data in the Neo4j database."""
        self._write_transaction(tx.cleanup)

    def close(self):
        """Close the connection to the Neo4j database."""
        self._driver.close()

    def _get_task_data_tuples(self, task_records):
        """Get a list of (task_record, hints, requirements, inputs, outputs) tuples.

        :param task_records: the database records of the tasks
        :type task_records: BoltStatementResult
        :rtype: list of (BoltStatementResult, list of Hint, list of Requirement)
        """
        with self._driver.session() as session:
            trecords = list(task_records)
            hint_records = [session.read_transaction(tx.get_task_hints,
                            task_id=rec["t"]["id"]) for rec in trecords]
            req_records = [session.read_transaction(tx.get_task_requirements,
                           task_id=rec["t"]["id"]) for rec in trecords]
            input_records = [session.read_transaction(tx.get_task_inputs,
                             task_id=rec["t"]["id"]) for rec in trecords]
            output_records = [session.read_transaction(tx.get_task_outputs,
                              task_id=rec["t"]["id"]) for rec in trecords]

        hints = [_reconstruct_hints(hint_record) for hint_record in hint_records]
        reqs = [_reconstruct_requirements(req_record) for req_record in req_records]
        inputs = [_reconstruct_task_inputs(input_record) for input_record in input_records]
        outputs = [_reconstruct_task_outputs(output_record) for output_record in output_records]

        return list(zip(trecords, hints, reqs, inputs, outputs))

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


def _reconstruct_requirements(req_records):
    """Reconstruct requirements by their records retrieved from Neo4j.

    :param req_records: the database record of the requirements
    :type req_records: BoltStatementResult
    :rtype: list of Requirement
    """
    recs = [req_record["r"] for req_record in req_records]
    return [Requirement(rec["class"], {k: v for k, v in rec.items() if k != "class"})
            for rec in recs]


def _reconstruct_hints(hint_records):
    """Reconstruct hints by their records retrieved from Neo4j.

    :param hint_records: the database record of the hints
    :type hint_records: BoltStatementResult
    :rtype: list of Hint
    """
    recs = [hint_record["h"] for hint_record in hint_records]
    return [Hint(rec["class"], {k: v for k, v in rec.items() if k != "class"}) for rec in recs]


def _reconstruct_workflow_inputs(input_records):
    """Reconstruct workflow inputs by their records retrieved from Neo4j.

    :param input_records: the database record of the inputs
    :type input_records: BoltStatementResult
    :rtype: list of InputParameter
    """
    recs = [input_record["i"] for input_record in input_records]
    return [InputParameter(rec["id"], rec["type"], rec["value"]) for rec in recs]


def _reconstruct_workflow_outputs(output_records):
    """Reconstruct workflow outputs by their records retrieved from Neo4j.

    :param output_records: the database record of the outputs
    :type output_records: BoltStatementResult
    :rtype: list of OutputParameter
    """
    recs = [output_record["o"] for output_record in output_records]
    return [OutputParameter(rec["id"], rec["type"], rec["value"], rec["source"]) for rec in recs]


def _reconstruct_task_inputs(input_records):
    """Reconstruct task inputs by their records retrieved from Neo4j.

    :param input_records: the database record of the inputs
    :type input_records: BoltStatementResult
    :rtype: list of StepInput
    """
    recs = [input_record["i"] for input_record in input_records]
    return [_reconstruct_task_input(rec) for rec in recs]


def _reconstruct_task_input(rec):
    """Reconstruct a task input by its record retrieved from Neo4j.

    :param rec: the database record of the input
    :type rec: BoltStatementResult
    :rtype: StepInput
    """
    return StepInput(rec["id"], rec["type"], rec["value"], rec["default"], rec["source"],
                     rec["prefix"], rec["position"], rec["value_from"])


def _reconstruct_task_outputs(output_records):
    """Reconstruct task outputs by their records retrieved from Neo4j.

    :param output_records: the database record of the outputs
    :type output_records: BoltStatementResult
    :rtype: list of StepOutput
    """
    recs = [output_record["o"] for output_record in output_records]
    return [_reconstruct_task_output(rec) for rec in recs]


def _reconstruct_task_output(rec):
    """Reconstruct a task output by its record retrieved from Neo4j.

    :param rec: the database record of the output
    :type rec: BoltStatementResult
    :rtype: StepOutput
    """
    return StepOutput(rec["id"], rec["type"], rec["value"], rec["glob"])


def _reconstruct_workflow(workflow_record, hints, requirements, inputs, outputs):
    """Reconstruct a Workflow object by its record retrieved from Neo4j.

    :param workflow_record: the database record of the workflow
    :type workflow_record: BoltStatementResult
    :param hints: the workflow hints
    :type hints: list of Hint
    :param requirements: the workflow requirements
    :type requirements: list of Requirement
    :param inputs: the workflow inputs
    :type inputs: list of InputParameter
    :param outputs: the workflow outputs
    :type outputs: list of OutputParameter
    :rtype: Workflow
    """
    rec = workflow_record["w"]
    return Workflow(name=rec["name"], hints=hints, requirements=requirements, inputs=inputs,
                    outputs=outputs, workflow_id=rec["id"])


def _reconstruct_task(task_record, hints, requirements, inputs, outputs):
    """Reconstruct a Task object by its record retrieved from Neo4j.

    :param task_record: the database record of the task
    :type task_record: BoltStatementResult
    :param hints: the task hints
    :type hints: list of Hint
    :param requirements: the task requirements
    :type requirements: list of Requirement
    :param inputs: the task inputs
    :type inputs: list of StepInput
    :param outputs: the task outputs
    :type outputs: list of StepOutput
    :rtype: Task
    """
    rec = task_record["t"]
    return Task(name=rec["name"], base_command=rec["base_command"], hints=hints,
                requirements=requirements, inputs=inputs, outputs=outputs, stdout=rec["stdout"],
                workflow_id=rec["workflow_id"], task_id=rec["id"])


def _reconstruct_metadata(metadata_record):
    """Reconstruct a dict containing the job description metadata retrieved from Neo4j.

    :param metadata_record: the database record of the metadata
    :type metadata_record: BoltStatementResult
    :param keys: the metadata keys to retrieve from the record
    :type keys: iterable of str
    :rtype: dict
    """
    rec = metadata_record["m"]
    return {key: val for key, val in rec.items() if key != "state"}

# pylama:ignore=E1129