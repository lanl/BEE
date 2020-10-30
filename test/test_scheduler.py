"""BEE Scheduler tests.

Tests of the BEE Scheduler module.
"""

import time

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.sched_types as sched_types
# import beeflow.common.data.wf_data as wf_data


class TestFCFS:
    """Test the FCFS algorithm.

    Test the FCFS algorithm.
    """
    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task.

        Test scheduling one task.
        """
        schedule_one_task(algorithms.FCFS())

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks.

        Test scheduling two tasks.
        """
        schedule_two_tasks(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available.

        Test scheduling a task with more resources required than available.
        """
        schedule_task_fail(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement.

        """
        schedule_task_gpus_req(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail.

        """
        schedule_task_gpus_req_fail(algorithms.FCFS())

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling six tasks.

        Test scheduling six tasks.
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
        resource = sched_types.Resource(id_='test-resource-1', nodes=4)

        tasks = [task1, task2, task3, task4, task5, task6]
        algorithms.FCFS().schedule_all(tasks, [resource])

        assert task1.allocations[0].id_ == 'test-resource-1'
        assert task1.allocations[0].start_time == 0
        assert task1.allocations[0].nodes == 1
        assert task2.allocations[0].id_ == 'test-resource-1'
        assert task2.allocations[0].start_time == 0
        assert task2.allocations[0].nodes == 1
        assert task3.allocations[0].id_ == 'test-resource-1'
        assert task3.allocations[0].start_time == 0
        assert task3.allocations[0].nodes == 1
        assert task4.allocations[0].id_ == 'test-resource-1'
        assert task4.allocations[0].start_time == 0
        assert task4.allocations[0].nodes == 1
        assert task5.allocations[0].id_ == 'test-resource-1'
        t = task2.requirements.max_runtime
        assert task5.allocations[0].start_time == t
        assert task5.allocations[0].nodes == 1
        assert task6.allocations[0].id_ == 'test-resource-1'
        assert task6.allocations[0].start_time == t
        assert task6.allocations[0].nodes == 1


class TestBackfill:
    """Test the Backfill algorithm.

    Test the Backfill algorithm.
    """

    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task.

        Test scheduling one task.
        """
        schedule_one_task(algorithms.Backfill())

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks.

        Test scheduling two tasks.
        """
        schedule_two_tasks(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available.

        Test scheduling a task with more resources required than available.
        """
        schedule_task_fail(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement.

        """
        schedule_task_gpus_req(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail.

        """
        schedule_task_gpus_req_fail(algorithms.Backfill())

    @staticmethod
    def test_schedule_three_tasks():
        """Test scheduling three tasks.

        Test scheduling three tasks.
        """
        requirements = {'max_runtime': 1, 'nodes': 1}
        task1 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-1',
                                 requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 2}
        task2 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-2',
                                 requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 1}
        task3 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-3',
                                 requirements=requirements)
        resource = sched_types.Resource(id_='resource-0',
                                        nodes=2)

        tasks = [task1, task2, task3]
        algorithms.Backfill().schedule_all(tasks, [resource])

        assert task1.allocations[0].id_ == 'resource-0'
        assert task1.allocations[0].nodes == 1
        assert task1.allocations[0].start_time == 0
        assert task2.allocations[0].id_ == 'resource-0'
        assert task2.allocations[0].nodes == 2
        assert (task2.allocations[0].start_time
                == task1.requirements.max_runtime)
        # Task 3 should have been backfillled, filling in an area before task
        # 2 can run
        assert task3.allocations[0].id_ == 'resource-0'
        assert task3.allocations[0].nodes == 1
        assert task3.allocations[0].start_time == 0

    @staticmethod
    def test_schedule_four_tasks():
        """Test scheduling four tasks.

        Test scheduling four tasks.
        """
        requirements = {'max_runtime': 2, 'nodes': 4}
        task1 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-0',
                                 requirements=requirements)
        requirements = {'max_runtime': 2, 'nodes': 8}
        task2 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-1',
                                 requirements=requirements)
        requirements = {'max_runtime': 3, 'nodes': 2}
        # This task should not be backfilled (too much time)
        task3 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-2',
                                 requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 2}
        # This task should be backfilled
        task4 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-3',
                                 requirements=requirements)
        resource1 = sched_types.Resource(id_='resource-0', nodes=2)
        resource2 = sched_types.Resource(id_='resource-1', nodes=2)
        resource3 = sched_types.Resource(id_='resource-2', nodes=2)
        resource4 = sched_types.Resource(id_='resource-3', nodes=2)

        tasks = [task1, task2, task3, task4]
        resources = [resource1, resource2, resource3, resource4]
        algorithms.Backfill().schedule_all(tasks, resources)

        assert len(task1.allocations) == 2
        assert all(a.start_time == 0 for a in task1.allocations)
        assert len(task2.allocations) == 4
        start_time = task1.requirements.max_runtime
        assert all(a.start_time == start_time for a in task2.allocations)
        # task3 should not have been backfilled (would have taken too
        # much time)
        assert len(task3.allocations) == 1
        start_time = (task1.requirements.max_runtime
                      + task2.requirements.max_runtime)
        assert task3.allocations[0].start_time == start_time
        # task4 should have been backfilled
        assert len(task4.allocations) == 1
        assert task4.allocations[0].start_time == 0

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling six tasks.

        Test scheduling six tasks.
        """
        requirements = {'max_runtime': 1, 'nodes': 1}
        task1 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-1',
                                 requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 4}
        task2 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-2',
                                 requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 1}
        task3 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-3',
                                 requirements=requirements)
        task4 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-4',
                                 requirements=requirements)
        task5 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-5',
                                 requirements=requirements)
        task6 = sched_types.Task(workflow_name='workflow-0',
                                 task_name='task-6',
                                 requirements=requirements)
        resource = sched_types.Resource(id_='resource-0',
                                        nodes=4)

        tasks = [task1, task2, task3, task4, task5, task6]
        algorithms.Backfill().schedule_all(tasks, [resource])

        assert task1.allocations[0].id_ == 'resource-0'
        assert task1.allocations[0].nodes == 1
        assert task1.allocations[0].start_time == 0
        assert task2.allocations[0].id_ == 'resource-0'
        assert task2.allocations[0].nodes == 4
        assert (task2.allocations[0].start_time
                == task1.requirements.max_runtime)
        # Task 3, 4 and 5 should have been backfillled, filling in an area
        # before task 2 can run
        assert task3.allocations[0].id_ == 'resource-0'
        assert task3.allocations[0].nodes == 1
        assert task3.allocations[0].start_time == 0
        assert task4.allocations[0].id_ == 'resource-0'
        assert task4.allocations[0].nodes == 1
        assert task4.allocations[0].start_time == 0
        assert task5.allocations[0].id_ == 'resource-0'
        assert task5.allocations[0].nodes == 1
        assert task5.allocations[0].start_time == 0
        # Task 6 should be scheduled to run last
        assert task6.allocations[0].id_ == 'resource-0'
        assert task6.allocations[0].nodes == 1
        t = task1.requirements.max_runtime + task2.requirements.max_runtime
        assert task6.allocations[0].start_time == t


class TestSJF:
    """Test SJF.

    Test SJF.
    """

    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task.

        Test scheduling one task.
        """
        schedule_one_task(algorithms.SJF)

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks.

        Test scheduling two tasks.
        """
        # schedule_two_tasks(algorithms.SJF)
        requirements = {'max_runtime': 3}
        task1 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-1', requirements=requirements)
        task2 = sched_types.Task(workflow_name='workflow-1',
                                 task_name='task-2', requirements=requirements)
        resource = sched_types.Resource(id_='test-resource-1', nodes=2)

        algorithms.SJF().schedule_all([task1, task2], [resource])

        assert task1.allocations[0].id_ == 'test-resource-1'
        assert task1.allocations[0].nodes == 1
        assert task2.allocations[0].id_ == 'test-resource-1'
        assert task2.allocations[0].nodes == 1
        # TODO: This test may need to change if the SJF algorithm is updated
        assert task1.allocations[0].start_time != task2.allocations[0].start_time

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available.

        Test scheduling a task with more resources required than available.
        """
        schedule_task_fail(algorithms.SJF())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement.

        """
        schedule_task_gpus_req(algorithms.SJF())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail.

        """
        schedule_task_gpus_req_fail(algorithms.SJF())


#
# Shared testing functions.
#

def schedule_one_task(algorithm):
    """Test scheduling one task.

    Test scheduling one task.
    """
    requirements = {'max_runtime': 3}
    task = sched_types.Task(workflow_name='workflow-1', task_name='task-1',
                            requirements=requirements)
    resource = sched_types.Resource(id_='test-resource-1', nodes=4)

    algorithm.schedule_all([task], [resource])

    assert task.allocations[0].id_ == 'test-resource-1'
    assert task.allocations[0].start_time == 0
    assert task.allocations[0].nodes == 1


def schedule_two_tasks(algorithm):
    """Test scheduling two tasks.

    Test scheduling two tasks.
    """
    requirements = {'max_runtime': 3}
    task1 = sched_types.Task(workflow_name='workflow-1',
                             task_name='task-1', requirements=requirements)
    task2 = sched_types.Task(workflow_name='workflow-1',
                             task_name='task-2', requirements=requirements)
    resource = sched_types.Resource(id_='test-resource-1', nodes=2)

    algorithm.schedule_all([task1, task2], [resource])

    assert task1.allocations[0].id_ == 'test-resource-1'
    assert task1.allocations[0].nodes == 1
    assert task1.allocations[0].start_time == 0
    assert task2.allocations[0].id_ == 'test-resource-1'
    assert task2.allocations[0].nodes == 1
    assert task2.allocations[0].start_time == 0


def schedule_task_fail(algorithm):
    """Test scheduling a task with more resources required than available.

    Test scheduling a task with more resources required than available.
    """
    requirements = {'max_runtime': 3, 'nodes': 10}
    task1 = sched_types.Task(workflow_name='workflow-1',
                             task_name='task-1', requirements=requirements)
    resource = sched_types.Resource(id_='test-resource-1', nodes=2)

    assert algorithm.schedule_all([task1], [resource]) is None
    # No allocations available
    assert not task1.allocations

def schedule_task_gpus_req(algorithm):
    """Test scheduling a task with the gpus requirement.

    """
    requirements = {
        'max_runtime': 10,
        'nodes': 10,
        'gpus': 4,
    }
    task1 = sched_types.Task(workflow_name='test-workflow', task_name='task-1',
                             requirements=requirements)
    resource1 = sched_types.Resource(id_='test-resource-1', nodes=20, gpus=0)
    resource2 = sched_types.Resource(id_='test-resource-2', nodes=20, gpus=20)

    algorithm.schedule_all([task1], [resource1, resource2])

    assert task1.allocations[0].id_ == 'test-resource-2'
    assert task1.allocations[0].nodes == 10
    assert task1.allocations[0].gpus == 4
    assert task1.allocations[0].start_time == 0

def schedule_task_gpus_req_fail(algorithm):
    """Test scheduling a task with the gpus requirement that should fail.

    """
    requirements = {
        'max_runtime': 10,
        'nodes': 10,
        'gpus': 10,
    }
    task1 = sched_types.Task(workflow_name='test-workflow', task_name='task-1',
                             requirements=requirements)
    resource1 = sched_types.Resource(id_='test-resource-1', nodes=20, gpus=0)

    algorithm.schedule_all([task1], [resource1])

    assert not task1.allocations
