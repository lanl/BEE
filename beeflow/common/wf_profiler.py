"""Workflow profiling code."""
import json
import time


class WorkflowProfiler:
    """Class for profiling a single workflow's execution."""

    def __init__(self, workflow_name, output_path):
        """Construct the workflow profiler class for a workflow."""
        self.workflow_name = workflow_name
        self.output_path = output_path
        self._state_changes = []
        self._scheduling_results = []

    def add_state_change(self, task, next_state):
        """Save a change of state for a task (at each task state change)."""
        self._state_changes.append({
            'task_id': task.id,
            'task_name': task.name,
            # State is not stored in the task object
            # 'previous_state': task.state,
            'next_state': next_state,
            'timestamp': int(time.time()),
        })

    def add_scheduling_results(self, tasks, resources, allocations):
        """Add scheduling results (given the set of available resources)."""
        self._scheduling_results.append({
            'tasks': tasks,
            'resources': resources,
            'allocations': dict(allocations),
            'timestamp': int(time.time()),
        })

    def save(self):
        """Save the workflow results (run on workflow completion)."""
        with open(self.output_path, 'w', encoding='utf-8') as fp:
            json.dump({
                'state_changes': self._state_changes,
                'scheduling_results': self._scheduling_results,
            }, fp=fp, indent=4)
