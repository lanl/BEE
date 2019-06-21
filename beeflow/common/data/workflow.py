"""Defines data structures for holding workflow data and metadata."""


class Workflow:
    """Data structure for holding workflow data and metadata."""

    def __init__(self, tasks, outputs):
        """Initialize a new workflow data structure.

        :param tasks (list): A list of Task instances
        :param outputs (list): A list of outputs (TO-DO: determine structure)
        """
        self._tasks = tasks
        self._outputs = outputs
