"""BEE Scheduler tests.

Tests of the BEE Scheduler module.
"""

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types
# import sched_types
import beeflow.common.data.wf_data as wf_data

def test_schedule_one_task():
    """Test scheduling one task."""
    task = sched_types.Task(workflow_name='workflow-1', task_name='task-1',
                            max_runtime=3)
    resource = sched_types.ResourceCollection(id_='test-resource-1', cores=4)
    allocation_store = allocation.AllocationStore()

    allocation_store.schedule(algorithms.FCFS, task, [resource])

    assert len(allocation_store.allocations) == 1
    assert allocation_store.allocations[0].workflow_name == task.workflow_name
    assert allocation_store.allocations[0].task_name == task.task_name
    assert len(allocation_store.allocations[0].resources) == 1
    assert allocation_store.allocations[0].resources[0].id_ == 'test-resource-1'
    assert allocation_store.allocations[0].resources[0].cores == 1
