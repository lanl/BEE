"""BEE Scheduler tests.

Unit tests for the BEE Scheduler.
"""

import time

import beeflow.scheduler.algorithms as algorithms
import beeflow.scheduler.task as task
import beeflow.scheduler.resource_allocation as resource_allocation


# TODO: Check scheduled jobs in the schedule_all() function.
# TODO: Add test cases for workflow dependencies
# TODO: Add tests cases for job state changes
class TestFCFS:
    """Test the FCFS algorithm."""
    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task."""
        schedule_one_task(algorithms.FCFS())

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks."""
        schedule_two_tasks(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available."""
        schedule_task_fail(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement."""
        schedule_task_gpus_req(algorithms.FCFS())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail."""
        schedule_task_gpus_req_fail(algorithms.FCFS())

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling six tasks."""
        requirements1 = {'max_runtime': 3}
        workflow_name = 'workflow-1'
        task1 = task.Task(workflow_name='workflow-1', job_name='task-1',
                          requirements=requirements1)
        task2 = task.Task(workflow_name='workflow-1', job_name='task-2',
                          requirements=requirements1)
        requirements2 = {'max_runtime': 4}
        task3 = task.Task(workflow_name='workflow-1', job_name='task-3',
                          requirements=requirements2)
        task4 = task.Task(workflow_name='workflow-1', job_name='task-4',
                          requirements=requirements2)
        task5 = task.Task(workflow_name='workflow-1', job_name='task-5',
                          requirements=requirements2)
        task6 = task.Task(workflow_name='workflow-1', job_name='task-6',
                          requirements=requirements2)
        resource = resource_allocation.Resource(id_='test-resource-1', nodes=4)

        tasks = [task1, task2, task3, task4, task5, task6]
        schedule = algorithms.FCFS().schedule_all(tasks, [resource])

        for task in [task1, task2, task3, task4]:
            alloc = schedule[workflow_name][task.job_name]
            assert alloc['after'] == {}
            # assert alloc['resources'][0].id_ == 'test-resource-1'
            assert resource.id_ in alloc['allocations']
            assert alloc['allocations'][resource.id_].nodes == 1
            # assert alloc['nodes'] == 1
        after = {
            workflow_name: [task.job_name for task in [task1, task2, task3, task4]],
        }
        for task in [task5, task6]:
            alloc = schedule[workflow_name][task.job_name]
            assert alloc['after'] == after
            assert alloc['nodes'] == 1
        """
        schedule[workflow_name][task1.job_name]['resources'][0].id_ == 'test-resource-1'
        schedule[workflow_name][task1.job_name][0].after == []

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
"""


class TestBackfill:
    """Test the Backfill algorithm."""

    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task."""
        schedule_one_task(algorithms.Backfill())

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks."""
        schedule_two_tasks(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available."""
        schedule_task_fail(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement."""
        schedule_task_gpus_req(algorithms.Backfill())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail."""
        schedule_task_gpus_req_fail(algorithms.Backfill())

    @staticmethod
    def test_schedule_three_tasks():
        """Test scheduling three tasks."""
        requirements = {'max_runtime': 1, 'nodes': 1}
        workflow_name = 'workflow-0'
        task1 = task.Task(workflow_name='workflow-0', job_name='task-1',
                          requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 2}
        task2 = task.Task(workflow_name='workflow-0', job_name='task-2',
                          requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 1}
        task3 = task.Task(workflow_name='workflow-0', job_name='task-3',
                          requirements=requirements)
        resource = resource_allocation.Resource(id_='resource-0', nodes=2)

        tasks = [task1, task2, task3]
        schedule = algorithms.Backfill().schedule_all(tasks, [resource])

        # Task 1
        alloc = schedule[workflow_name][task1.job_name]
        assert not alloc['after']
        assert 'resource-0' in alloc['allocations']
        assert alloc['allocations']['resource-0'].nodes == 1
        #assert alloc['resources'][0].id_ == 'resource-0'
        #assert alloc['resources'][]
        # Task 2
        alloc = schedule[workflow_name][task2.job_name]
        assert all(task.job_name in alloc['after'][workflow_name] for task in [task1, task3])
        assert 'resource-0' in alloc['allocations']
        assert alloc['allocations']['resource-0'].nodes == 2
        # Task 3 (should have been backfilled)
        alloc = schedule[workflow_name][task3.job_name]
        assert not alloc['after']
        assert 'resource-0' in alloc['allocations']
        assert alloc['allocations']['resource-0'].nodes == 1
        """
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
"""

    @staticmethod
    def test_schedule_four_tasks():
        """Test scheduling four tasks."""
        requirements = {'max_runtime': 2, 'nodes': 4}
        task1 = task.Task(workflow_name='workflow-0', job_name='task-0',
                          requirements=requirements)
        requirements = {'max_runtime': 2, 'nodes': 8}
        task2 = task.Task(workflow_name='workflow-0', job_name='task-1',
                          requirements=requirements)
        requirements = {'max_runtime': 3, 'nodes': 2}
        # This task should not be backfilled (too much time)
        task3 = task.Task(workflow_name='workflow-0', job_name='task-2',
                          requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 2}
        # This task should be backfilled
        task4 = task.Task(workflow_name='workflow-0', job_name='task-3',
                          requirements=requirements)
        resource1 = resource_allocation.Resource(id_='resource-0', nodes=2)
        resource2 = resource_allocation.Resource(id_='resource-1', nodes=2)
        resource3 = resource_allocation.Resource(id_='resource-2', nodes=2)
        resource4 = resource_allocation.Resource(id_='resource-3', nodes=2)

        tasks = [task1, task2, task3, task4]
        resources = [resource1, resource2, resource3, resource4]
        schedule = algorithms.Backfill().schedule_all(tasks, resources)

        # Task 1
        alloc = schedule[workflow_name][task1.job_name]
        assert len(alloc['allocations']) == 2
        assert not alloc['after']
        # Task 2
        alloc = schedule[workflow_name][task2.job_name]
        assert len(alloc['allocations']) == 4
        assert all(task.job_name in alloc['after'][workflow_name] for task in [task1, task4])
        # Task 3 (should not have been backfilled)
        alloc = schedule[workflow_name][task3.job_name]
        assert len(alloc['allocations']) == 1
        assert all(task.job_name in alloc['after'][workflow_name]
                   for task in [task1, task2, task4])
        # Task 4 (should have been backfilled)
        alloc = schedule[workflow_name][task4.job_name]
        assert len(alloc['allocations']) == 1
        assert not alloc['after']
        """
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
"""

    @staticmethod
    def test_schedule_six_tasks():
        """Test scheduling six tasks."""
        requirements = {'max_runtime': 1, 'nodes': 1}
        task1 = task.Task(workflow_name='workflow-0', job_name='task-1',
                          requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 4}
        task2 = task.Task(workflow_name='workflow-0', job_name='task-2',
                          requirements=requirements)
        requirements = {'max_runtime': 1, 'nodes': 1}
        task3 = task.Task(workflow_name='workflow-0', job_name='task-3',
                          requirements=requirements)
        task4 = task.Task(workflow_name='workflow-0', job_name='task-4',
                          requirements=requirements)
        task5 = task.Task(workflow_name='workflow-0', job_name='task-5',
                          requirements=requirements)
        task6 = task.Task(workflow_name='workflow-0', job_name='task-6',
                          requirements=requirements)
        resource = resource_allocation.Resource(id_='resource-0', nodes=4)

        tasks = [task1, task2, task3, task4, task5, task6]
        schedule = algorithms.Backfill().schedule_all(tasks, [resource])

        # Task 1
        alloc = schedule[task1.workflow_name][task1.job_name]
        assert resource.id_ in alloc['allocations']
        assert alloc['allocations'][resource.id_].nodes == task1.requirements.nodes
        assert not alloc['after']
        # Task 2
        alloc = schedule[task2.workflow_name][task2.job_name]
        assert resource.id_ in alloc['allocations']
        assert alloc['allocations'][resource.id_].nodes == task2.requirements.nodes
        assert all(task.job_name in alloc['after'][task.workflow_name]
                   for task in [task1, task3, task4, task5])
        # Tasks 3-5 should have been backfilled before task 2
        for task in [task3, task4, task5]:
            alloc = schedule[task.workflow_name][task.job_name]
            assert resource.id_ in alloc['allocations']
            assert alloc['allocations'][resource.id_].nodes == task.requirements.nodes
            assert not alloc['after']
        # Task 6 runs last
        alloc = schedule[task6.workflow_name][task6.job_name]
        assert resource.id_ in alloc['allocations']
        assert alloc['allocations'][resource.id_].nodes == task.requirements.nodes
        assert task2.job_name in alloc['after'][task2.workflow_name]
        """
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
"""


class TestSJF:
    """Test SJF."""

    @staticmethod
    def test_schedule_one_task():
        """Test scheduling one task."""
        schedule_one_task(algorithms.SJF)

    @staticmethod
    def test_schedule_two_tasks():
        """Test scheduling two tasks."""
        # schedule_two_tasks(algorithms.SJF)
        requirements = {'max_runtime': 3}
        task1 = task.Task(workflow_name='workflow-1', job_name='task-1',
                          requirements=requirements)
        task2 = task.Task(workflow_name='workflow-1', job_name='task-2',
                          requirements=requirements)
        resource = resource_allocation.Resource(id_='test-resource-1', nodes=2)

        schedule = algorithms.SJF().schedule_all([task1, task2], [resource])

        # These can be allocated at the same time, since the resource has two
        # nodes
        for task in [task1, task2]:
            alloc = schedule[task.workflow_name][task.job_name]
            assert resource.id_ in alloc['allocations']
            assert alloc['allocations'][resource.id_].nodes == task.requirements.nodes
            assert not alloc['after']
        """
        assert len(task1.allocations) == 1
        assert task1.allocations[0].id_ == 'test-resource-1'
        assert task1.allocations[0].nodes == 1
        assert len(task2.allocations) == 1
        assert task2.allocations[0].id_ == 'test-resource-1'
        assert task2.allocations[0].nodes == 1
        # These can be allocated at the same time, since the resource has two
        # nodes
        assert (task1.allocations[0].start_time
                == task2.allocations[0].start_time)
"""

    @staticmethod
    def test_schedule_task_fail():
        """Test scheduling a task with more resources required than available."""
        schedule_task_fail(algorithms.SJF())

    @staticmethod
    def test_schedule_task_gpus_req():
        """Test scheduling a task with a gpus requirement."""
        schedule_task_gpus_req(algorithms.SJF())

    @staticmethod
    def test_schedule_task_gpus_req_fail():
        """Test scheduling a task with a gpus requirement that should fail."""
        schedule_task_gpus_req_fail(algorithms.SJF())


#
# Shared testing functions.
#

def schedule_one_task(algorithm):
    """Test scheduling one task."""
    requirements = {'max_runtime': 3}
    task1 = task.Task(workflow_name='workflow-1', job_name='task-1',
                      requirements=requirements)
    resource = resource_allocation.Resource(id_='test-resource-1', nodes=4)

    schedule = algorithm.schedule_all([task1], [resource])

    alloc = schedule[task1.workflow_name][task1.job_name]
    assert resource.id_ in alloc['allocations']
    assert alloc['allocations'][resource.id_].nodes == task1.requirements.nodes
    """
    assert task1.allocations[0].id_ == 'test-resource-1'
    assert task1.allocations[0].start_time == 0
    assert task1.allocations[0].nodes == 1
"""


def schedule_two_tasks(algorithm):
    """Test scheduling two tasks."""
    requirements = {'max_runtime': 3}
    task1 = task.Task(workflow_name='workflow-1', job_name='task-1',
                      requirements=requirements)
    task2 = task.Task(workflow_name='workflow-1', job_name='task-2',
                      requirements=requirements)
    resource = resource_allocation.Resource(id_='test-resource-1', nodes=2)

    schedule = algorithm.schedule_all([task1, task2], [resource])

    for task in [task1, task2]:
        alloc = schedule[task.workflow_name][task.job_name]
        assert resource.id_ in alloc['allocations']
        assert alloc['allocations'][resource.id_].nodes == task.nodes
        # All tasks run at the same time
        assert not alloc['after']
    """
    alloc = _get_alloc(schedule, task1)
    assert resource.id_ in alloc['allocations']
    assert alloc['allocations'][resource.id_].nodes == task1.nodes
    assert task1.allocations[0].id_ == 'test-resource-1'
    assert task1.allocations[0].nodes == 1
    assert task1.allocations[0].start_time == 0
    assert task2.allocations[0].id_ == 'test-resource-1'
    assert task2.allocations[0].nodes == 1
    assert task2.allocations[0].start_time == 0
"""


def schedule_task_fail(algorithm):
    """Test scheduling a task with more resources required than available.

    Test scheduling a task with more resources required than available.
    """
    requirements = {'max_runtime': 3, 'nodes': 10}
    task1 = task.Task(workflow_name='workflow-1', job_name='task-1',
                      requirements=requirements)
    resource = resource_allocation.Resource(id_='test-resource-1', nodes=2)

    schedule = algorithm.schedule_all([task1], [resource])

    # No allocations should be available
    alloc = schedule[task1.workflow_name][task1.job_name]
    assert not alloc['allocations']
    """
    # assert algorithm.schedule_all([task1], [resource]) is None
    # No allocations available
    assert not task1.allocations
"""

def schedule_task_gpus_req(algorithm):
    """Test scheduling a task with the gpus requirement."""
    requirements = {
        'max_runtime': 10,
        'nodes': 10,
        'gpus_per_node': 4,
    }
    task1 = task.Task(workflow_name='test-workflow', job_name='task-1',
                      requirements=requirements)
    resource1 = resource_allocation.Resource(id_='test-resource-1', nodes=20,
                                             gpus_per_node=0)
    # I really doubt that any node would ever actually have 20 gpus
    resource2 = resource_allocation.Resource(id_='test-resource-2', nodes=20,
                                             gpus_per_node=20)

    schedule = algorithm.schedule_all([task1], [resource1, resource2])

    alloc = schedule[task1.workflow_name][task1.job_name]
    assert resource2.id_ in alloc['allocations']
    res_alloc = alloc['allocations'][resource2.id_]
    assert res_alloc.nodes == task1.requirements.nodes
    # TODO: res_alloc may need to contain information about how many GPUs were allocated
    """
    assert task1.allocations[0].id_ == 'test-resource-2'
    assert task1.allocations[0].nodes == 10
    assert task1.allocations[0].start_time == 0
"""

def schedule_task_gpus_req_fail(algorithm):
    """Test scheduling a task with the gpus requirement that should fail."""
    requirements = {
        'max_runtime': 10,
        'nodes': 10,
        'gpus_per_node': 10,
    }
    task1 = task.Task(workflow_name='test-workflow', job_name='task-1',
                      requirements=requirements)
    resource1 = resource_allocation.Resource(id_='test-resource-1', nodes=20,
                                             gpus_per_node=0)

    schedule = algorithm.schedule_all([task1], [resource1])

    alloc = schedule[task1.workflow_name][task1.job_name]
    assert not alloc['allocations']


#
# Test runtime estimation
#

import beeflow.scheduler.runtime_estimator as runtime_estimator


def test_runtime_estimator_interface():
    """Test runtime estimator interface."""
    # TODO: Need other information like input data size
    requirements = {
        'nodes': 10,
        'gpus_per_node': 10,
    }
    task = task.Task(workflow_name='test', job_name='test', requirements=requirements)

    # The state stores task runtime information and useful estimate data
    # (state will most likely correspond to Redis in the future)
    state = {}
    estimate = runtime_estimator.estimate(state, task)

    assert estimate > 0 and estimate < 100
