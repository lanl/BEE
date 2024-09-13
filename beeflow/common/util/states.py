"""Workflow and Task state values."""


class WorkflowStates:
    """Workflow status values."""

    INITIALIZING = 'INITIALIZING'
    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    PAUSED = 'PAUSED'
    RESUME = 'RESUME'
    CANCELLED = 'CANCELLED'


class TaskStates:
    """Task status values."""

    PENDING = 'PENDING'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    PAUSED = 'PAUSED'
    CANCELLED = 'CANCELLED'
