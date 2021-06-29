"""Simple task-resource affinity algorithm."""

import random


# XXX: Hack until we can use Redis for this
prev_schedules = {}


def find_best_resource(dep_tasks):
    """Find the best resource, given a set of dependent tasks."""
    resources = {}
    for dep_task in dep_tasks:
        res_name = prev_schedules[dep_task]
        resources[res_name] = resources[res_name] + 1 if res_name in resources else 1
    if resources:
        return min(resources, key=lambda res_name: resources[res_name])
    return None


def schedule_all(tasks, resources, **kwargs):
    """Schedule all tasks onto the resources using the affinity algorithm."""
    schedule = {}
    for task_name in tasks:
        task_reqs = tasks[task_name]
        # Get the list of dependent tasks
        dep_tasks = task_reqs['deps']
        res_name = find_best_resource(dep_tasks)
        if res_name is None:
            # Choose a random resource
            res_names = [res_name for res_name in resources]
            res_name = res_names[random.randint(0, len(res_names) - 1)]
            # Check if the task has an affinity for a resource
            if 'affinity' in task_reqs and task_reqs['affinity'] in res_names:
                # TODO: Log this some how
                res_name = task_reqs['affinity']
        # Schedule the task
        schedule[task_name] = {
            # Time slots are per-resource
            'time_slot': 0,	# XXX: the time slot should be based on what tasks can run at once and those that should run later
            'resource': res_name,
        }
        # Store the scheduled allocation
        prev_schedules[task_name] = res_name
    return schedule
