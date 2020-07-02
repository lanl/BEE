"""BEE Scheduler tests.

Tests of the BEE Scheduler module.
"""

import time

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
        requirements = {'max_runtime': 3}
        task = sched_types.Task(workflow_name='workflow-1', task_name='task-1',
                                requirements=requirements)
        resource = sched_types.Resource(id_='test-resource-1', cores=4)

        allocation.schedule_all(algorithms.FCFS, [task], [resource])

        assert task.allocations[0].id_ == 'test-resource-1'
        assert task.allocations[0].start_time == int(time.time())
        assert task.allocations[0].cores == 1

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks.

        """
        requirements = {'max_runtime': 3}
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', requirements=requirements)
        task2 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-2', requirements=requirements)
        resource = sched_types.Resource(id_='test-resource-1', cores=2)

        allocation.schedule_all(algorithms.FCFS, [task1, task2], [resource])

        current_time = int(time.time())
        assert task1.allocations[0].id_ == 'test-resource-1'
        assert task1.allocations[0].cores == 1
        assert task1.allocations[0].start_time == current_time
        assert task2.allocations[0].id_ == 'test-resource-1'
        assert task2.allocations[0].cores == 1
        assert task2.allocations[0].start_time == current_time

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available.

        """
        requirements = {'max_runtime': 3, 'cores': 10}
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', requirements=requirements)
        resource = sched_types.Resource(id_='test-resource-1', cores=2)

        assert (allocation.schedule_all(algorithms.FCFS, [task1], [resource])
                is None)
        # No allocations available
        assert not task1.allocations

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling two tasks.

        """
        requirements1 = {'max_runtime': 3}
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1',
                                 requirements=requirements1)
        task2 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-2',
                                 requirements=requirements1)
        requirements2 = {'max_runtime': 4}
        task3 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-3',
                                 requirements=requirements2)
        task4 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-4',
                                 requirements=requirements2)
        task5 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-5',
                                 requirements=requirements2)
        task6 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-6',
                                 requirements=requirements2)
        resource = sched_types.Resource(id_='test-resource-1', cores=4)

        tasks = [task1, task2, task3, task4, task5, task6]
        allocation.schedule_all(algorithms.FCFS, tasks, [resource])

        current_time = int(time.time())
        assert task1.allocations[0].id_ == 'test-resource-1'
        assert task1.allocations[0].start_time == current_time
        assert task1.allocations[0].cores == 1
        assert task2.allocations[0].id_ == 'test-resource-1'
        assert task2.allocations[0].start_time == current_time
        assert task2.allocations[0].cores == 1
        assert task3.allocations[0].id_ == 'test-resource-1'
        assert task3.allocations[0].start_time == current_time
        assert task3.allocations[0].cores == 1
        assert task4.allocations[0].id_ == 'test-resource-1'
        assert task4.allocations[0].start_time == current_time
        assert task4.allocations[0].cores == 1
        assert task5.allocations[0].id_ == 'test-resource-1'
        t = current_time + task3.requirements['max_runtime']
        assert (task5.allocations[0].start_time == t)
        assert task5.allocations[0].cores == 1
        assert task6.allocations[0].id_ == 'test-resource-1'
        assert (task6.allocations[0].start_time == t)
        assert task6.allocations[0].cores == 1
