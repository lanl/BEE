#!/usr/bin/env python3
import allocation

# TODO: Perhaps structure these tests into classes based on the
#       feature being tested.

def test_partition_insert_empty_0():
    """Test inserting into a empty partition."""
    partition = allocation.Partition(name='test-partition-0')
    task = allocation.Task(name='task-0', runtime=2)

    partition.insert(task, start_time=0)

    assert len(partition.slots) == 1
    assert not partition.slots[0].open
    assert partition.slots[0].task.name == 'task-0'
    assert partition.slots[0].start_time == 0
    assert partition.slots[0].runtime == 2

def test_partition_insert_empty_1():
    """Test inserting into an empty partition at a specific time."""
    partition = allocation.Partition(name='test-partition-0')
    task = allocation.Task(name='task-0', runtime=2)

    partition.insert(task, start_time=3)

    assert len(partition.slots) == 2
    assert partition.slots[0].open
    assert partition.slots[0].start_time == 0
    assert partition.slots[0].runtime == 3
    assert not partition.slots[1].open
    assert partition.slots[1].task.name == 'task-0'
    assert partition.slots[1].start_time == 3
    assert partition.slots[1].runtime == 2

def test_partition_insert_non_empty_0():
    """Test inserting into a non-empty partition."""
    partition = allocation.Partition(name='test-partition-0')
    task1 = allocation.Task(name='task-0', runtime=2)
    partition.insert(task1, start_time=3)
    task2 = allocation.Task(name='task-1', runtime=2)

    partition.insert(task2)

    assert len(partition.slots) == 3
    assert not partition.slots[0].open
    assert partition.slots[0].task.name == 'task-1'
    assert partition.slots[0].start_time == 0
    assert partition.slots[0].runtime == 2
    assert partition.slots[1].open
    assert partition.slots[1].start_time == 2
    assert partition.slots[1].runtime == 1
    assert not partition.slots[2].open
    assert partition.slots[2].task.name == 'task-0'
    assert partition.slots[2].start_time == 3
    assert partition.slots[2].runtime == 2

def test_partition_insert_non_empty_1():
    """Test inserting into a non-empty partition with two tasks."""
    partition = allocation.Partition(name='test-partition-0')
    task1 = allocation.Task(name='task-0', runtime=2)
    partition.insert(task1)
    task2 = allocation.Task(name='task-1', runtime=2)
    partition.insert(task2, start_time=4)
    task3 = allocation.Task(name='task-2', runtime=2)

    partition.insert(task3)

    assert len(partition.slots) == 3
    assert not partition.slots[0].open
    assert partition.slots[0].task.name == 'task-0'
    assert partition.slots[0].start_time == 0
    assert partition.slots[0].runtime == 2
    assert not partition.slots[1].open
    assert partition.slots[1].task.name == 'task-2'
    assert partition.slots[1].start_time == 2
    assert partition.slots[1].runtime == 2
    assert not partition.slots[2].open
    assert partition.slots[2].task.name == 'task-1'
    assert partition.slots[2].start_time == 4
    assert partition.slots[2].runtime == 2

def test_partition_insert_non_empty_2():
    """Test inserting into a non-empty partition with a slot left over."""
    partition = allocation.Partition(name='test-partition-0')
    task1 = allocation.Task(name='task-0', runtime=2)
    partition.insert(task1)
    task2 = allocation.Task(name='task-1', runtime=2)
    partition.insert(task2, start_time=6)
    task3 = allocation.Task(name='task-2', runtime=2)

    partition.insert(task3)

    assert len(partition.slots) == 4
    assert not partition.slots[0].open
    assert partition.slots[0].task.name == 'task-0'
    assert partition.slots[0].start_time == 0
    assert partition.slots[0].runtime == 2
    assert not partition.slots[1].open
    assert partition.slots[1].task.name == 'task-2'
    assert partition.slots[1].start_time == 2
    assert partition.slots[1].runtime == 2
    assert partition.slots[2].open
    assert partition.slots[2].start_time == 4
    assert partition.slots[2].runtime == 2
    assert not partition.slots[3].open
    assert partition.slots[3].task.name == 'task-1'
    assert partition.slots[3].start_time == 6
    assert partition.slots[3].runtime == 2


def test_partition_fit_empty_0():
    """Test method fit() on an empty partition."""
    partition = allocation.Partition(name='test-partition-2')
    task = allocation.Task(name='task', runtime=44)

    t = partition.fit(task)

    assert t == 0

def test_partition_fit_empty_1():
    """Test method fit() on an empty partition with a start time."""
    partition = allocation.Partition(name='test-partition-2')
    task = allocation.Task(name='task', runtime=44)

    t = partition.fit(task, start_time=1)

    assert t == 1

def test_partition_fit_non_empty_0():
    """Test method fit() on a non-empty partition."""
    partition = allocation.Partition(name='test-partition-2')
    task1 = allocation.Task(name='task-0', runtime=44)
    partition.insert(task1, start_time=2)
    task2 = allocation.Task(name='task-1', runtime=2)

    t = partition.fit(task2)

    assert t == 0

def test_partition_fit_non_empty_1():
    """Test method fit on a non-empty partition with a small timeslot."""
    partition = allocation.Partition(name='test-partition-2')
    task1 = allocation.Task(name='task-0', runtime=44)
    partition.insert(task1, start_time=2)
    task2 = allocation.Task(name='task-1', runtime=60)

    t = partition.fit(task2)

    assert t == 46


def test_fcfs_one_task_one_partition():
    """Test the fcfs algorithm with a single task and a single partition."""
    task = allocation.Task(name='task-0', runtime=10)
    workflow = allocation.Workflow(name='workflow-0')
    workflow.insert(level=0, task=task)
    cluster = allocation.Cluster(name='cluster-0')
    partition = allocation.Partition(name='partition-0')
    cluster.insert_partition(partition)

    provision = allocation.fcfs(workflow, [cluster], 0)

    assert len(provision) == 1
    assert provision['task-0'].partition_name == 'partition-0'
    assert provision['task-0'].cluster_name == 'cluster-0'
    assert provision['task-0'].start_time == 0
    assert provision['task-0'].task.name == 'task-0'
    assert provision['task-0'].task.runtime == 10

def test_fcfs_two_tasks_one_partition():
    """Test the fcfs algorithm with two tasks and a single partition."""
    task1 = allocation.Task(name='task-0', runtime=10)
    task2 = allocation.Task(name='task-1', runtime=10)
    workflow = allocation.Workflow(name='workflow-0')
    workflow.insert(level=0, task=task1)
    workflow.insert(level=1, task=task2)
    cluster = allocation.Cluster(name='cluster-0')
    partition = allocation.Partition(name='partition-0')
    cluster.insert_partition(partition)

    provision = allocation.fcfs(workflow, [cluster], 0)

    assert len(provision) == 2
    assert provision['task-0'].partition_name == 'partition-0'
    assert provision['task-0'].cluster_name == 'cluster-0'
    assert provision['task-0'].start_time == 0
    assert provision['task-0'].task.name == 'task-0'
    assert provision['task-1'].partition_name == 'partition-0'
    assert provision['task-1'].cluster_name == 'cluster-0'
    assert provision['task-1'].start_time == 10
    assert provision['task-1'].task.name == 'task-1'
