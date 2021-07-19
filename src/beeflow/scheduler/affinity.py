"""Simple task-resource affinity algorithm."""

import random


# XXX: Hack until we can use Redis for this
prev_schedules = {}


def find_best_resource(dep_tasks):
    """Find the best resource, given a set of dependent tasks."""
    resource_counts = {}
    for dep_task in dep_tasks:
        res_name = prev_schedules[dep_task]
        resource_counts[res_name] = resource_counts[res_name] + 1 if res_name in resource_counts else 1
    if resource_counts:
        return min(resource_counts, key=lambda res_name: resource_counts[res_name])
    return None


def schedule_all(tasks, resources, **kwargs):
    """Schedule all tasks onto the resources using the affinity algorithm."""
    schedule = {}
    # List of resources scheduled for the system
    scheduled = {resource: [] for resource in resources}
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
        scheduled[res_name].append(task_name)
        already_scheduled_count = len(scheduled[res_name])
        print(resources)
        nodes = resources[res_name]['nodes']
        # Schedule the task
        schedule[task_name] = {
            # The time slot determines when a task should run
            'time_slot': int(already_scheduled_count / nodes),
            'resource': res_name,
        }
        # Store the scheduled allocation
        prev_schedules[task_name] = res_name
    return schedule
