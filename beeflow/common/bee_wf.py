"""High-level workflow management interface."""

from beeflow.common.gdb.bee_gdb import GraphDatabaseInterface


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabaseInterface.
    """

    def __init__(self, inputs, outputs):
        """Initialize the BEE workflow interface.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self._gdb_interface = GraphDatabaseInterface()
        self.load_workflow(inputs, outputs)

    def load_workflow(self, inputs, outputs):
        """Load a new BEE workflow.

        :param inputs: the workflow inputs
        :type inputs: TBD
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self._gdb_interface.load_workflow(inputs, outputs)

    def initialize_workflow(self):
        """Initialize the workflow."""
        self._gdb_interface.initialize_workflow()

    def get_dependents(self, task):
        """Get the dependent tasks of a specified task.

        :param task: the task whose dependents to retrieve
        :type task: instance of Task
        :rtype: set of Task instances
        """
        return self._gdb_interface.get_dependents(task)

    def finalize_workflow(self):
        """Finalize the workflow."""
        self._gdb_interface.finalize_workflow()
