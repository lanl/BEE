"""High-level workflow management interface."""

from beeflow.common.gdb.bee_gdb import GraphDatabase


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabase class.
    """

    def __init__(self, inputs, outputs):
        """Initialize the BEE workflow interface.

        :param inputs (TBD): workflow inputs
        :param outputs (TBD): workflow outputs
        """
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

    # Dependencies can be accessed directly through the
    # Task object, so this might be redundant
    # def get_dependents(self, task):
    #     """Get the dependent tasks of a specified task.

    #     :param task (Task): The task whose dependents to get
    #     """
    #     self._gdb.get_dependents_dag(task)

    def finalize_workflow(self):
        """Finish the workflow."""
        self._gdb.finalize_workflow_dag()
