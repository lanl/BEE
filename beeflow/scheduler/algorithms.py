"""Code implementing various scheduling algorithms.

Code implementing scheduling algorithms, such as FCFS, Backfill, etc.
"""

import abc
import random
import time
import tensorflow as tf

import beeflow.scheduler.sched_types as sched_types
import beeflow.scheduler.mars as mars
import beeflow.scheduler.util as util


class Algorithm(abc.ABC):
    """Scheduling algorithm abstract class.

    Base abstract class for implementing a scheduling algorithm.
    """

    @staticmethod
    @abc.abstractmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule all tasks with the implemented algorithm.

        Schedule all tasks with the implemented algorithm.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """

class SJF(Algorithm):
    """Shortest job first algorithm.

    Class holding scheduling code for runing the shortest job first algorithm.
    """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with SJF.

        Schedule a list of independent tasks with SFJ.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources list of instance of sched_types.Resource
        """
        # Note this doesn't allocate aggregate resources but only singular
        # resources unlike the other algorithms
        # allocations = []
        start_time = int(time.time())
        tasks = tasks[:]
        # Sort by max_runtime
        tasks.sort(key=lambda t: t.requirements.max_runtime)
        resources = resources[:]
        while tasks:
            task = tasks.pop()
            # Check if it can run
            # remaining = sched_types.rsum(*resources)
            if not any(res.fits_requirements(task.requirements)
                       for res in resources):
                # Can't run on given resources
                continue
            # max_runtime = task.requirements.max_runtime
            for res in resources:
                if res.fits_requirements(task.requirements):
                    alloc = res.allocate(res, [], task.requirements, start_time)
                    task.allocations = [alloc]
            start_time += task.requirements.max_runtime
            # for time, runtime, resource in allocations:
            #    # Calculate the overlaping allocations
            #    overlap = [alloc for alloc in allocations if alloc[0] < time and alloc[0] + ]
            # TODO


class FCFS(Algorithm):
    """FCFS scheduling algorithm.

    This class holds the scheduling code used for the FCFS
    scheduling algorithm.
    """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with FCFS.

        Schedule an entire list of tasks using FCFS. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        allocations = []
        start_time = int(time.time())
        # Continue while there are still tasks to schedule
        for task in tasks:
            # Check if the task can run at all
            remaining = sched_types.rsum(*resources)
            if not remaining.fits_requirements(task.requirements):
                # Can't run this task at all
                continue
            max_runtime = task.requirements.max_runtime
            while True:
                overlap = util.calculate_overlap(allocations, start_time,
                                                 max_runtime)
                remaining = sched_types.diff(sched_types.rsum(*resources),
                                             sched_types.rsum(*overlap))
                if remaining.fits_requirements(task.requirements):
                    allocs = util.allocate_aggregate(resources, overlap, task,
                                                     start_time)
                    allocations.extend(allocs)
                    task.allocations = allocs
                    break
                # Set the next time increment to check
                start_time = min(a.start_time + a.max_runtime
                                 for a in overlap)
        # TODO: Update time based on runtime of algorithm


class Backfill(Algorithm):
    """Backfill scheduling algorithm.

    This class holds the scheduling code used for the Backfill
    scheduling algorithm.
    """

    @staticmethod
    def schedule_all(tasks, resources, **kwargs):
        """Schedule a list of independent tasks with Backfill.

        Schedule an entire list of tasks using Backfill. Tasks that
        cannot be allocated will be left with an empty allocations
        property.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of sched_types.Resource
        """
        tasks = tasks[:]
        # TODO: This time may be invalidated if the algorithm
        # takes too long
        current_time = int(time.time())
        allocations = []
        while tasks:
            # Get a task to schedule
            task = tasks.pop(0)
            total = sched_types.rsum(*resources)
            if not total.fits_requirements(task.requirements):
                continue
            # Can this task run immediately?
            start_time = current_time
            max_runtime = task.requirements.max_runtime
            overlap = util.calculate_overlap(allocations, start_time,
                                             max_runtime)
            remaining = util.calculate_remaining(resources, overlap)
            if remaining.fits_requirements(task.requirements):
                allocs = util.allocate_aggregate(resources, overlap, task,
                                                 start_time)
                allocations.extend(allocs)
                task.allocations = allocs
                continue
            # This job must run later, so find the shadow time (the earliest
            # time at which the job can run)
            shadow_time = current_time
            times = [a.start_time + a.max_runtime for a in allocations]
            times.sort()
            for start_time in times:
                overlap = util.calculate_overlap(allocations, start_time,
                                                 max_runtime)
                remaining = util.calculate_remaining(resources, overlap)
                if remaining.fits_requirements(task.requirements):
                    shadow_time = start_time
                    allocs = util.allocate_aggregate(resources, overlap, task,
                                                     start_time)
                    allocations.extend(allocs)
                    task.allocations = allocs
                    break
            # Backfill tasks
            tasks_left = []
            for task in tasks:
                times = [current_time]
                times.extend(a.start_time + a.max_runtime for a in allocations)
                max_runtime = task.requirements.max_runtime
                # Ensure that the task will finish before the shadow time
                times = [t for t in times if (t + max_runtime) <= shadow_time]
                times.sort()
                # Determine when it can run (if it can be backfilled)
                for start_time in times:
                    overlap = util.calculate_overlap(allocations, start_time,
                                                     max_runtime)
                    remaining = util.calculate_remaining(resources, overlap)
                    if remaining.fits_requirements(task.requirements):
                        allocs = util.allocate_aggregate(resources, overlap,
                                                         task, start_time)
                        allocations.extend(allocs)
                        task.allocations = allocs
                        break
                # Could not backfill this task
                if not task.allocations:
                    tasks_left.append(task)
            # Reset the tasks to the remaining list
            tasks = tasks_left
        # TODO: Update time based on runtime of algorithm


class MARS(Algorithm):
    """MARS Scheduler.

    MARS Scheduler.
    """
    @staticmethod
    def load(mars_model='model', **kwargs):
        """Load the model.

        Load the model.
        """
        MARS.actor, MARS.critic = mars.load_models(mars_model)

    @staticmethod
    def policy(actor, critic, task, tasks, possible_allocs):
        """Evaluate the policy function to find scheduling of task.

        Evaluate the policy function with the model task.
        :param actor: actor used for scheduling
        :type actor: instance of mars.ActorModel
        :param critic: critic used during training
        :type critic: instance of mars.CriticModel
        :param task: task to get the scheduling policy for
        :type task: instance of Task
        :param possible_allocs: possible allocations for the task
        :type possible_allocs: list of instance of Allocation
        :rtype: int, index of allocation to use
        """
        # No possible allocations
        if not possible_allocs:
            return -1
        # Convert the task and possible_allocs into a vector
        # for input into the policy function.
        # TODO: Input should include the specific task
        vec = mars.workflow2vec(task, tasks)
        vec = tf.constant([vec])
        # Convert the result into an action index
        pl = [float(n) for n in actor.call(vec)[0]]
        a = pl.index(max(pl))
        a = (float(a) / len(pl)) * (len(possible_allocs) - 1)
        return int(a)

    @staticmethod
    def schedule_all(tasks, resources, mars_model='model', **kwargs):
        """Schedule a list of tasks on the given resources.

        Schedule a full list of tasks on the given resources. Note: MARS.load()
        must have been called previously.
        :param tasks: list of tasks to schedule
        :type tasks: list of instance of Task
        :param resources: list of resources
        :type resources: list of instance of Resource
        :param mars_model: the mars model path
        :type mars_model: str
        """
        # TODO: Set the path somewhere else
        # actor, critic = mars.load_models(mars_model)
        allocations = []
        for task in tasks:
            possible_allocs = build_allocation_list(task, tasks, resources,
                                                    curr_allocs=allocations)
            pi = MARS.policy(MARS.actor, MARS.critic, task, tasks,
                             possible_allocs)
            # -1 indicates no allocation found
            if pi != -1:
                allocs = possible_allocs[pi]
                allocations.extend(allocs)
                task.allocations = allocs
        # TODO: Update time based on runtime of algorithm


class AlgorithmWrapper:
    """Algorithm wrapper class.

    Algorithm wrapper class to be used as a wrap to log the task scheduling
    data for future training and other extra information.
    """

    def __init__(self, cls, logfile='schedule_log.txt', **kwargs):
        """Algorithm wrapper class constructor.

        Algorithm wrapper class constructor.
        :param cls: class to pass operations onto
        :type cls: Python class
        :param logfile: name of logfile to write to
        :type logfile: str
        :param kwargs: key word arguments to pass to schedule_all()
        :type kwargs: instance of dict
        """
        self.cls = cls
        self.logfile = logfile
        self.kwargs = kwargs

    def schedule_all(self, tasks, resources):
        """Schedule all tasks using the internal class and log results.

        Schedule all of the tasks with the internal class and write the
        results out to a log file.
        """
        self.cls.schedule_all(tasks, resources, **self.kwargs)
        with open(self.logfile, 'a') as fp:
            print('; Log start at', time.time(), file=fp)
            curr_allocs = []
            for task in tasks:
                possible_allocs = build_allocation_list(task, tasks, resources,
                                                        curr_allocs)
                # Find the value of a - the index of the allocation for this
                # task
                a = -1
                # TODO: Calculation of a needs to change
                if task.allocations:
                    start_time = task.allocations[0].start_time
                    # a should be the first alloc with the same start_time
                    for i, alloc in enumerate(possible_allocs):
                        if alloc[0].start_time == start_time:
                            a = i
                            break
                vec = mars.workflow2vec(task, tasks)
                # vec.append(a)
                # TODO: Add more information for calculating reward (i.e. CPU
                # usage, memory usage, resources available, etc.)

                # Output in SWF format
                # TODO: These variables may not be all in the right spot and
                # some may be missing as well
                print(-1, -1, -1, task.requirements.max_runtime,
                      task.requirements.cores, task.requirements.max_runtime,
                      task.requirements.mem, task.requirements.cores, -1,
                      task.requirements.mem, task.requirements.mem, -1,
                      -1, -1, -1, -1, -1, -1, -1, file=fp)
                # print(*vec, file=fp)
                curr_allocs.extend(task.allocations)


def build_allocation_list(task, tasks, resources, curr_allocs):
    """Build a list of allocations for a task.

    Build a list of allocations for a task.
    :param task:
    :type task:
    :param tasks:
    :type tasks:
    :param resources:
    :type resources:
    """
    times = set(t.allocations[0].start_time + t.requirements.max_runtime
                for t in tasks if t.allocations)
    times = list(times)
    # Add initial start time
    times.append(int(time.time()))
    times.sort()
    allocations = []
    for start_time in times:
        overlap = util.calculate_overlap(curr_allocs, start_time,
                                         task.requirements.max_runtime)
        remaining = sched_types.diff(sched_types.rsum(*resources),
                                     sched_types.rsum(*overlap))
        if remaining.fits_requirements(task.requirements):
            # TODO: Ensure that these allocations are not final (in other
            # other words, if the algorithm decides to pick one and not the
            # other, later on, we don't want there to be conflicts)
            allocs = util.allocate_aggregate(resources, overlap, task,
                                             start_time)
            allocations.append(allocs)
    return allocations


# TODO: Perhaps this value should be a config value
MEDIAN = 2


def load(**kwargs):
    """Load data needed by the algorithms.

    Load data needed by the algorithms.
    """
    MARS.load(**kwargs)


def choose(tasks, use_mars=False, algorithm=None, **kwargs):
    """Choose which algorithm to run at this point.

    Determine which algorithm class needs to run and return it.
    :param tasks: list of tasks:
    :type tasks: list of instance of Task
    :rtype: class derived from Algorithm (not an instance)
    """
    # TODO: Correctly choose based on size of the workflow
    # return Logger(Backfill)
    if algorithm == 'fcfs':
        print('Using FCFS')
        cls = FCFS
    elif algorithm == 'mars':
        print('Using MARS')
        cls = MARS
    elif algorithm == 'backfill':
        print('Using Backfill')
        cls = Backfill
    elif algorithm == 'sjf':
        print('Using SJF')
        cls = SJF
    else:
        if use_mars:
            cls = Backfill if len(tasks) < MEDIAN else MARS
        else:
            cls = Backfill
    return AlgorithmWrapper(cls, **kwargs)
