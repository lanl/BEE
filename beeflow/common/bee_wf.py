"""High-level workflow management interface."""

from beeflow.common.dag.bee_dag import GraphDatabase


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabaseDriver class.
    """

    def __init__(self, inputs, outputs):
        """Initialize the BEE workflow interface."""
        self._gdb = GraphDatabase()
        self.load_workflow(inputs, outputs)

    def load_workflow(self, inputs, outputs):
        """Load a new BEE workflow.

        :param inputs (list): Workflow inputs
        :param outputs (list): Workflow outputs
        """
        self._gdb.load_workflow_dag(inputs, outputs)

    def initialize_workflow(self):
        """Initialize the workflow."""
        self._gdb.initialize_workflow_dag()

    def get_dependents(self, task):
        """Get the dependent tasks of a specified task.

        :param task (Task): The task whose dependents to get
        """
        self._gdb.get_dependents_dag(task)

    def finalize_workflow(self):
        """Finish the workflow."""
        self._gdb.finalize_workflow_dag()
