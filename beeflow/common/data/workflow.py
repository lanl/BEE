"""Defines data structures for holding workflow data and metadata."""


class Workflow:
    """Data structure for holding workflow data and metadata."""

    def __init__(self, tasks, outputs):
        """Initialize a new workflow data structure.

        :param tasks: the workflow tasks
        :type tasks: set of Task instances
        :param outputs: the workflow outputs
        :type outputs: TBD
        """
        self._tasks = tasks
        self._outputs = outputs
