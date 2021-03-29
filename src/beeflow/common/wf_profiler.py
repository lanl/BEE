"""Workflow profiling code."""
import json
import time
import os


class WorkflowProfiler:
    """Class for profiling a single workflow's execution."""

    def __init__(self, workflow_name, save_dir):
        """WorkflowProfiler constructor."""
        self._workflow_name = workflow_name
        # TODO: Put this is in the config file
        profile_fname = '%s-profile-%.20i.json' % (workflow_name, int(time.time()))
        self._profile_fname = os.path.join(save_dir, profile_fname)
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

    def add_scheduling_results(self, resources, allocations):
        """Add scheduling results (given the set of available resources)."""
        self._scheduling_results.append({
            'resources': resources,
            'allocations': allocations,
            'timestamp': int(time.time()),
        })

    def save(self):
        """Save the workflow results (run on workflow completion)."""
        with open(self._profile_fname, 'w') as fp:
            json.dump({
                'state_changes': self._state_changes,
                'scheduling_results': self._scheduling_results,
            }, fp=fp, indent=4)
