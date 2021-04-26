
import abc


class Interface(abc.ABC):
    """Interface class for interacting with the Task Manager."""

    @staticmethod
    @abc.abstractmethod
    def schedule(tasks):
        """Schedule a list of tasks."""

    @staticmethod
    @abc.abstractmethod
    def start_time(alloc):
        """Return the start time of this allocation."""

    @abc.abstractmethod
    def submit(tasks, allocation):
        """Submit these tasks to the Task Manager."""


# TODO: This design is not necessarily the best since it doesn't take into
# account when tasks finish early
class RunQueue:
    """Class for managing a queue of tasks to run."""

    def __init__(self, iface):
        """RunQueue constructor."""
        # Callbacks
        self._iface = iface
        # List of tasks to be scheduled
        self._queue = []
        # List of tasks already scheduled
        self._scheduled = []
        # IDs of currently running tasks
        self._running = set()

    def _get_task_ids(self):
        """Return an iterator over all task IDs in the RunQueue."""
        # IDs of unscheduled tasks
        for qtasks in self._queue:
            for qtask in qtasks:
                yield qtask.id
        # IDs of scheduled tasks
        for sitem in self._scheduled:
            for stask_id in sitem['tasks']:
                yield stask_id
        # IDs of running tasks
        for task_id in self._running:
            yield task_id

    @property
    def count(self):
        """Return the number of tasks in the queue."""
        # return sum(1 for qitem in self._queue for task in qitem['tasks'])
        #return (sum(1 for qtasks in self._queue for qtask in qtasks)
        #        + sum(1 for stasks in self._scheduled for stask in stasks['tasks']))
        return (sum(len(qtasks) for qtasks in self._queue)
                + sum(len(sitem['tasks']) for sitem in self._scheduled) + len(self._running))

    @property
    def run_count(self):
        """Return the number of running tasks."""
        return len(self._running)

    def is_running(self, task_id):
        """Return True if the given task is running."""
        return task_id in self._running

    def complete(self, task):
        """Complete a Task (remove it from the running set)."""
        self._running.discard(task.id)

    def enqueue(self, tasks):
        """Add a list of unscheduled tasks to the queue."""
        # Remove tasks that are already in the queue
        tasks = [task for task in tasks if task.id not in self._get_task_ids()]
        # print('enqueue =', [task.name for task in tasks])
        if tasks:
            self._queue.append(tasks)

    def run_tasks(self):
        """Schedule and run any tasks that are able to run."""
        # assert self._queue or self._scheduled
        if not self._queue and not self._scheduled:
            return

        if self._running:
            return
        if not self._scheduled:
            # Need to schedule some tasks
            tasks = self._queue.pop(0)
            allocation = self._iface.schedule(tasks)
            self._scheduled.append({'tasks': {task.id: task for task in tasks},
                                    'allocation': allocation})

        sitem = self._scheduled[0]
        tasks = sitem['tasks']
        allocation = sitem['allocation']
        start_times = set(self._iface.start_time(allocation[task_id]) for task_id in allocation)
        start_times = list(start_times)
        start_times.sort()
        min_start_time = min(start_times)
        tasks_to_run = [tasks[task_id] for task_id in tasks
                        if self._iface.start_time(allocation[task_id]) == min_start_time]
        allocs_to_run = {task.id: allocation[task.id] for task in tasks_to_run}
        # Submit the tasks
        self._iface.submit(tasks_to_run, allocs_to_run)
        # Set the tasks as running
        self._running.update(task.id for task in tasks_to_run)
        # Remove tasks and allocations from the queue
        for task in tasks_to_run:
            del tasks[task.id]
            del allocation[task.id]
        # Remove the item if there are no more tasks to run
        if not tasks:
            del self._scheduled[0]


"""
        assert self._queue
        # Check if a previous allocation is still running
        if self._running:
            return

        if allocation is not None:
            self._running.update(task.id for task in tasks)
            submit_tasks_tm(tasks, allocation)
        else:
            qitem = self._queue.pop(0)
            tasks = qitem['tasks']
            allocation = qitem['allocation']
            # Need to schedule tasks
            sched_tasks = tasks_to_sched(tasks)
            allocation = submit_tasks_scheduler(sched_tasks)
            # Profiling
            profiler.add_scheduling_results(sched_tasks, rm.resource_ids, rm.get(), allocation)
            start_times = set(allocation[task_id][0]['start_time']
                              for task_id in allocation if allocation[task_id])
            start_times = list(start_times)
            start_times.sort()
            # Get the list of tasks that are scheduled
            tasks_by_start_time = [
                [task for task in tasks if allocation[task.id] and allocation[task.id]['start_time'] == start_time]
                for start_time in start_times
            ]

            #tasks_by_start_time = [
            #    start_time: [
            #        task for task in tasks
            #    ]
            #]
        return





        # TODO: Need to account for tasks that cannot be scheduled
        if not self._queue:
            return
        qitem = self._queue.pop(0)
        # Check if we can immediately run the tasks (if nothing is running right now)
        ready = not self._running
        print(self._queue)
        print(self._running)
        # Get the tasks and allocation from the qitem
        tasks = qitem['tasks']
        allocation = qitem['allocation']
        if allocation is None:
            # Schedule the tasks
            sched_tasks = tasks_to_sched(tasks)
            allocation = submit_tasks_scheduler(sched_tasks)
            # Store scheduling results for profiling
            profiler.add_scheduling_results(sched_tasks, rm.resource_ids, rm.get(), allocation)
            # Get all the scheduled start times
            start_times = set(allocation[task_id][0]['start_time']
                              for task_id in allocation if allocation[task_id])
            # Order tasks by their start times
            items = {
                start_time: [
                    task for task in tasks
                    if allocation[task.id] and allocation[task.id][0]['start_time'] == start_time
                ] for start_time in start_times
            }
            # Sort the start times
            start_times = list(start_times)
            start_times.sort(reverse=True)
            print(start_times)
            # Go over the start times from highest to lowest
            for start_time in start_times:
                tasks = items[start_time]
                if not tasks:
                    continue
                allocs = {task.id: allocation[task.id] for task in tasks}
                if start_time == 0 and ready:
                    # Launch tasks that can be launched now
                    self._running.update(task.id for task in tasks)
                    submit_tasks_tm(tasks, allocs)
                elif len(tasks) > 0:
                    # Add tasks that can't run yet to the queue
                    self._queue.insert(0, {'tasks': tasks, 'allocation': allocs})
        elif ready:
            self._running.update(task.id for task in tasks)
            submit_tasks_tm(tasks, allocation)
"""
