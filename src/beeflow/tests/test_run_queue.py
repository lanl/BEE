"""Tests of the RunQueue class."""
import uuid

import beeflow.common.run_queue as run_queue


class FakeTask:
    """A fake task for the RunQueue to deal with."""

    def __init__(self, start_time=0):
        """FakeTask constructor."""
        self.id = uuid.uuid4()
        self.start_time = start_time


class RunQueueInterface(run_queue.Interface):
    """RunQueue interface for scheduling tasks with a start time."""

    @staticmethod
    def schedule(tasks):
        """Schedule tasks."""
        return {task.id: {'start_time': task.start_time} for task in tasks}

    @staticmethod
    def start_time(alloc):
        """Return the start time of an allocation."""
        return alloc['start_time']

    @staticmethod
    def submit(tasks, allocation):
        """Submit tasks to the fake Task Manager."""
        assert all(task.id in allocation for task in tasks)


def test_run_queue_empty():
    """Test creating an empty run queue."""
    #def profile_fn():
    #    pass
    #def schedule_fn(tasks):
    #    """Task scheduling function."""
    #    pass

    #def start_time_fn():
    #    return 0

    rq = run_queue.RunQueue(RunQueueInterface)

    assert rq.count == 0


def test_run_queue_one_task_enqueue():
    """Test enqueueing one task."""
    # rq = run_queue.RunQueue(profile_fn, schedule_fn, start_time_fn)
    rq = run_queue.RunQueue(RunQueueInterface)
    tasks = [FakeTask()]

    rq.enqueue(tasks)

    assert rq.count == 1


def test_run_queue_one_task_run_tasks():
    """Test running one task."""
    rq = run_queue.RunQueue(RunQueueInterface)
    tasks = [FakeTask()]
    rq.enqueue(tasks)

    rq.run_tasks()

    assert rq.count == 1


def test_run_queue_one_task_complete():
    """Test completing one task."""
    rq = run_queue.RunQueue(RunQueueInterface)
    tasks = [FakeTask()]
    rq.enqueue(tasks)
    rq.run_tasks()

    rq.complete(tasks[0])

    assert rq.count == 0


def test_run_queue_many_tasks_same_start_time_complete_all():
    """Test running and completing many tasks."""
    rq = run_queue.RunQueue(RunQueueInterface)
    tasks = [FakeTask() for i in range(32)]
    rq.enqueue(tasks)
    rq.run_tasks()

    # Complete all of the tasks
    for task in tasks:
        rq.complete(task)

    assert rq.count == 0


def test_run_queue_many_tasks_different_start_time_complete_all():
    """Test running many tasks that are scheduled with a different start time."""
    rq = run_queue.RunQueue(RunQueueInterface)
    tasks = [FakeTask(start_time=i) for i in range(32)]
    rq.enqueue(tasks)

    for task in tasks:
        rq.run_tasks()
        assert rq.run_count == 1
        assert rq.is_running(task.id)
        rq.complete(task)

    assert rq.count == 0

def test_multiple_enqueue_and_run():
    """Test enqueueing multiple times and running."""
    rq = run_queue.RunQueue(RunQueueInterface)

    rq.enqueue([FakeTask(), FakeTask()])
    rq.run_tasks()
    rq.enqueue([FakeTask()])

    assert rq.count == 3
