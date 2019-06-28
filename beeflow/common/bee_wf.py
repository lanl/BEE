"""High-level workflow management interface."""

from beeflow.common.gdb.bee_gdb import GraphDatabaseInterface


class WorkflowInterface:
    """Interface for managing BEE workflows.

    Delegates its work to a GraphDatabaseInterface instance.
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
        """Initialize a BEE workflow."""
        self._gdb_interface.initialize_workflow()

    def get_dependent_tasks(self, task):
        """Get the dependents of a task in the BEE workflow.

        :param task: the task whose dependents to obtain
        :type task: instance of Task
        :rtype: set of Task instances
        """
        return self._gdb_interface.get_dependent_tasks(task)

    def finalize_workflow(self):
        """Finalize the BEE workflow."""
        self._gdb_interface.finalize_workflow()
