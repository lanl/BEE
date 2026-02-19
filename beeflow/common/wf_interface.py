"""High-level BEE workflow management interface.

Delegates its work to a GraphDatabaseInterface instance.
"""

import re
import glob
from beeflow.common import log as bee_logging
from beeflow.common.gdb.neo4j_driver import Neo4jDriver
from beeflow.common import expr

log = bee_logging.setup(__name__)


class WorkflowInterface:
    """Interface for manipulating workflows."""

    def __init__(self, wf_id, gdb_driver=Neo4jDriver):
        """Initialize the Workflow interface.

        Initializing this interface automatically attempts to
        connect to the graph database.

        :param gdb_interface: the gdb interface
        """
        # Connect to the graph database
        self._gdb_driver = gdb_driver
        self._workflow_id = wf_id

    @property
    def workflow_id(self):
        """Retrieve the workflow ID from the workflow interface.

        If workflow ID is not populated, this grabs it from the database.

        If no workflow is loaded, None is returned.
        :rtype: str
        """
        if self._workflow_id is None:
            workflow, _ = self.get_workflow()
            self._workflow_id = workflow.id

        return self._workflow_id

    def initialize_workflow(self, workflow):
        """Begin construction of a BEE workflow.

        :param workflow: the workflow object
        :type workflow: Workflow
        """
        if workflow.requirements is None:
            workflow.requirements = []
        if workflow.hints is None:
            workflow.hints = []

        self._workflow_id = workflow.id
        # Load the new workflow into the graph database
        self._gdb_driver.initialize_workflow(workflow)

    def execute_workflow(self):
        """Begin execution of a BEE workflow."""
        self._gdb_driver.execute_workflow(self._workflow_id)

    def pause_workflow(self):
        """Pause the execution of a BEE workflow."""
        self._gdb_driver.pause_workflow(self._workflow_id)

    def resume_workflow(self):
        """Resume the execution of a paused BEE workflow."""
        self._gdb_driver.resume_workflow(self._workflow_id)

    def add_task(self, task):
        """Add a new task to a BEE workflow.

        :param task: the name of the file to which to redirect stderr
        :type task: Task
        """
        # Immutable default arguments
        if task.inputs is None:
            task.inputs = []
        if task.outputs is None:
            task.outputs = []
        if task.requirements is None:
            task.requirements = []
        if task.hints is None:
            task.hints = []

        # Load the new task into the graph database
        self._gdb_driver.load_task(task)

    def restart_task(self, task, checkpoint_file):
        """Restart a failed BEE workflow task.

        The task must have a beeflow:CheckpointRequirement hint. If there are no
        remaining retry attemps (num_tries = 0) then the graph database is
        unmodified and this method returns None.

        :param task: the task to restart
        :type task: Task
        :param checkpoint_file: the task checkpoint file
        :rtype: Task or None
        """
        for hint in task.hints:
            if hint.class_ == "beeflow:CheckpointRequirement":
                num_tries = hint.params.get("num_tries")
                if num_tries is None or num_tries > 0:
                    # None = unlimited restarts, don't decrement
                    if num_tries is not None:
                        hint.params["num_tries"] -= 1
                    hint.params["bee_checkpoint_file__"] = checkpoint_file
                    break
                # num_tries == 0, no more restart attempts
                self.set_task_state(task.id, "FAILED")
                self.set_workflow_state("FAILED")
                return None
        else:
            log.error("invalid task for checkpoint restart")
            raise ValueError("invalid task for checkpoint restart")

        new_task = task.copy(update={"new_id": True})
        # Pattern match on task name
        # Append (1) if not in name already
        # Increment number on each restart
        match = re.search(r"-(\d+)$", new_task.name)
        if not match:
            new_task.name += "-1"
        else:
            i = int(match.group(1))
            new_task.name = re.sub(r"-(\d+)$", f"-{i + 1}", new_task.name)
        metadata = self.get_task_metadata(task.id)
        self._gdb_driver.restart_task(task, new_task)
        self.set_task_metadata(new_task.id, metadata)
        self.set_task_state(task.id, "RESTARTED")
        self.set_task_state(new_task.id, "READY")
        return new_task

    def finalize_task(self, task):
        """Mark a BEE workflow task as completed.

        This method also automatically deduces what tasks are now
        runnable, updating their states to ready and returning a
        list of the runnable tasks.

        :param task: the task to finalize
        :type task: Task
        :rtype: list of Task
        """
        self.evaluate_output_expression(task.id)
        self._gdb_driver.finalize_task(task)
        self._gdb_driver.initialize_ready_tasks(self._workflow_id)
        return self._gdb_driver.get_ready_tasks(self._workflow_id)

    def get_task_by_id(self, task_id):
        """Get a task by its Task ID.

        :param task_id: the task's ID
        :type task_id: str
        :rtype: Task
        """
        return self._gdb_driver.get_task_by_id(task_id)

    def get_workflow(self):
        """Get a loaded BEE workflow.

        Returns a tuple of (workflow_description, tasks)

        :rtype: tuple of (Workflow, list of Task)
        """
        workflow = self._gdb_driver.get_workflow_description(self._workflow_id)
        tasks = self._gdb_driver.get_workflow_tasks(self._workflow_id)
        return workflow, tasks

    def get_tasks(self):
        """Get all tasks in the workflow.

        :rtype: list of Task
        """
        return self._gdb_driver.get_workflow_tasks(self._workflow_id)

    def get_workflow_outputs(self):
        """Get the outputs from a BEE workflow.

        :rtype: list of OutputParameter
        """
        workflow = self._gdb_driver.get_workflow_description(self._workflow_id)
        return workflow.outputs

    def get_workflow_state(self):
        """Get the value of the workflow state.

        :rtype: str
        """
        state = self._gdb_driver.get_workflow_state(self._workflow_id)
        return state

    def set_workflow_state(self, state):
        """Set workflow's current state.

        :param state: the new state of the workflow
        :type state: str
        """
        self._gdb_driver.set_workflow_state(self._workflow_id, state)

    def get_ready_tasks(self):
        """Get ready tasks from a BEE workflow.

        :rtype: list of Task
        """
        return self._gdb_driver.get_ready_tasks(self._workflow_id)

    def get_dependent_tasks(self, task_id):
        """Get the dependents of a task in a BEE workflow.

        :param task: the task whose dependents to retrieve
        :type task: Task
        :rtype: list of Task
        """
        return self._gdb_driver.get_dependent_tasks(task_id)

    def get_task_state(self, task_id):
        """Get the state of the task in a BEE workflow.

        :param task: the task whose state to retrieve
        :type task: Task
        :rtype: str
        """
        return self._gdb_driver.get_task_state(task_id)

    def set_task_state(self, task_id, state):
        """Set the state of the task in a BEE workflow.

        This method should not be used to set a task as completed.
        finalize_task() should instead be used.

        :param task_id: the id of task whose state to set
        :type task_id: str
        :param state: the new state of the task
        :type state: str
        """
        self._gdb_driver.set_task_state(task_id, state)

    def get_task_metadata(self, task_id):
        """Get the job description metadata of a task in a BEE workflow.

        :param task: the task whose metadata to retrieve
        :type task: Task
        :rtype: dict
        """
        return self._gdb_driver.get_task_metadata(task_id)

    def set_task_metadata(self, task_id, metadata):
        """Set the job description metadata of a task in a BEE workflow.

        This method should not be used to update task state.
        set_task_state() or finalize_task() should instead be used.

        :param task: the task whose metadata to set
        :type task: Task
        :param metadata: the job description metadata
        :type metadata: dict
        """
        self._gdb_driver.set_task_metadata(task_id, metadata)

    def get_task_input(self, task_id, input_id):
        """Get a task input object.

        :param task: the task whose input to retrieve
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :rtype: StepInput
        """
        return self._gdb_driver.get_task_input(task_id, input_id)

    def set_task_input(self, task_id, input_id, value):
        """Set the value of a task input.

        :param task: the task whose input to set
        :type task: Task
        :param input_id: the ID of the input
        :type input_id: str
        :param value: str or int or float
        """
        self._gdb_driver.set_task_input(task_id, input_id, value)

    def get_task_output(self, task_id, output_id):
        """Get a task output object.

        :param task: the task whose output to retrieve
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :rtype: StepOutput
        """
        return self._gdb_driver.get_task_output(task_id, output_id)

    def set_task_output(self, task_id, output_id, value):
        """Set the value of a task output.

        :param task: the task whose output to set
        :type task: Task
        :param output_id: the ID of the output
        :type output_id: str
        :param value: the output value to set
        :type value: str or int or float
        """
        self._gdb_driver.set_task_output(task_id, output_id, value)

    def workflow_completed(self):
        """Return true if all of a workflow's final tasks have completed, else false.

        :rtype: bool
        """
        return self._gdb_driver.workflow_completed(self._workflow_id)

    def get_workflow_final_state(self):
        """Get final state of the workflow.

        :rtype: Optional[str]
        """
        return self._gdb_driver.get_workflow_final_state(self._workflow_id)

    def cancelled_workflow_completed(self):
        """Return true if all a cancelled workflow's scheduled tasks have completed, else false.

        :rtype: bool
        """
        return self._gdb_driver.cancelled_workflow_completed(self._workflow_id)

    def remove_workflow(self):
        """Remove the workflow from the graph database."""
        self._gdb_driver.remove_workflow(self._workflow_id)
        self._workflow_id = None

    def export_graphml(self):
        """Export a BEE workflow as a graphml."""
        self._gdb_driver.export_graphml(self._workflow_id)

    def evaluate_output_expression(self, task_id):
        """
        Evaluate javascript expresssions in workflow output specification"""
        task = self.get_task_by_id(task_id)
        input_pairs = {input.id: input.value for input in task.inputs}
        for output in task.outputs:
            if output.glob:
                val = expr.eval_output(input_pairs, output.glob)
                if val is not None:
                    self._gdb_driver.set_task_output_glob(task_id, output.id, val)
                    output.glob = val
                if output.type in {"String", "str", "string"}:
                    globs = glob.glob(output.glob)
                    if len(globs) > 0:
                        with open(globs[0], 'r', encoding='UTF-8') as f:
                            str_output = f.read()
                        self._gdb_driver.set_task_output(task_id, output.id, str_output)
                elif output.type in {"int", "integer", "Integer"}:
                    globs = glob.glob(output.glob)
                    if len(globs) > 0:
                        with open(globs[0], 'r', encoding='UTF-8') as f:
                            try:
                                int_output = int(f.read())
                            except ValueError:
                                int_output = None
                        self._gdb_driver.set_task_output(task_id, output.id, int_output)
                elif output.type in {"float", "Float", "FLOAT"}:
                    globs = glob.glob(output.glob)
                    if len(globs) > 0:
                        with open(globs[0], 'r', encoding='UTF-8') as f:
                            try:
                                float_output = float(f.read())
                            except ValueError:
                                float_output = None
                        self._gdb_driver.set_task_output(task_id, output.id, float_output)
                else:
                    self._gdb_driver.set_task_output(task_id, output.id, output.glob)
            else:
                self._gdb_driver.set_task_output(task_id, output.id, "ready")
