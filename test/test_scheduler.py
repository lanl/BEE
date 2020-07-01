"""BEE Scheduler tests.

Tests of the BEE Scheduler module.
"""

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.allocation as allocation
import beeflow.scheduler.sched_types as sched_types
import beeflow.common.data.wf_data as wf_data


class TestFCFS:
    """Test the FCFS algorithm.

    """

    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task.

        """
        task = sched_types.Task(workflow_name='workflow-1',
                                task_name='task-1', max_runtime=3)
        resource = sched_types.ResourceCollection(id_='test-resource-1',
                                                  cores=4)
        allocation_store = allocation.AllocationStore()

        allocation_store.schedule(algorithms.FCFS, task, [resource])

        assert len(allocation_store.allocations) == 1
        assert (allocation_store.allocations[0].workflow_name
                == task.workflow_name)
        assert allocation_store.allocations[0].task_name == task.task_name
        assert len(allocation_store.allocations[0].resources) == 1
        assert (allocation_store.allocations[0].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[0].resources[0].cores == 1

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks.

        """
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', max_runtime=3)
        task2 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-2', max_runtime=3)
        resource = sched_types.ResourceCollection(id_='test-resource-1',
                                                  cores=2)
        allocation_store = allocation.AllocationStore()

        allocation_store.schedule(algorithms.FCFS, task1, [resource])
        allocation_store.schedule(algorithms.FCFS, task2, [resource])

        assert len(allocation_store.allocations) == 2
        assert (allocation_store.allocations[0].workflow_name
                == task1.workflow_name)
        assert allocation_store.allocations[0].task_name == task1.task_name
        assert len(allocation_store.allocations[0].resources) == 1
        assert (allocation_store.allocations[0].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[0].resources[0].cores == 1

        assert (allocation_store.allocations[1].workflow_name
                == task2.workflow_name)
        assert allocation_store.allocations[1].task_name == task2.task_name
        assert len(allocation_store.allocations[1].resources) == 1
        assert (allocation_store.allocations[1].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[1].resources[0].cores == 1

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available.

        """
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', max_runtime=3, cores=10)
        resource = sched_types.ResourceCollection(id_='test-resource-1',
                                                  cores=2)
        allocation_store = allocation.AllocationStore()

        assert (allocation_store.schedule(algorithms.FCFS, task1, [resource])
                is None)

        assert allocation_store.allocations == []

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling two tasks.

        """
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', max_runtime=3)
        task2 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-2', max_runtime=3)
        task3 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-3', max_runtime=4)
        task4 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-4', max_runtime=4)
        task5 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-5', max_runtime=4)
        task6 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-6', max_runtime=4)
        resource = sched_types.ResourceCollection(id_='test-resource-1',
                                                  cores=4)
        allocation_store = allocation.AllocationStore()

        allocation_store.schedule(algorithms.FCFS, task1, [resource])
        allocation_store.schedule(algorithms.FCFS, task2, [resource])
        allocation_store.schedule(algorithms.FCFS, task3, [resource])
        task1.status = sched_types.TaskStatus.COMPLETED
        allocation_store.update_allocation(task1)
        task2.status = sched_types.TaskStatus.COMPLETED
        allocation_store.update_allocation(task2)
        task3.status = sched_types.TaskStatus.COMPLETED
        allocation_store.update_allocation(task3)
        allocation_store.schedule(algorithms.FCFS, task4, [resource])
        allocation_store.schedule(algorithms.FCFS, task5, [resource])
        allocation_store.schedule(algorithms.FCFS, task6, [resource])

        assert len(allocation_store.allocations) == 3
        assert (allocation_store.allocations[0].workflow_name
                == task4.workflow_name)
        assert allocation_store.allocations[0].task_name == task4.task_name
        assert len(allocation_store.allocations[0].resources) == 1
        assert (allocation_store.allocations[0].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[0].resources[0].cores == 1

        assert (allocation_store.allocations[1].workflow_name
                == task5.workflow_name)
        assert allocation_store.allocations[1].task_name == task5.task_name
        assert len(allocation_store.allocations[1].resources) == 1
        assert (allocation_store.allocations[1].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[1].resources[0].cores == 1

        assert (allocation_store.allocations[2].workflow_name
                == task6.workflow_name)
        assert allocation_store.allocations[2].task_name == task6.task_name
        assert len(allocation_store.allocations[2].resources) == 1
        assert (allocation_store.allocations[2].resources[0].id_
                == 'test-resource-1')
        assert allocation_store.allocations[2].resources[0].cores == 1
