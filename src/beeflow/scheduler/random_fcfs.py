"""Random FCFS algorithm."""

import random

from beeflow.cli import log


def schedule_all(tasks, resources):
    """Schedule all resources using a random FCFS algorithm."""
    schedule = {}
    # Create a list of all virtual nodes
    nodes = [res_name for res_name in resources for i in range(resources[res_name]['nodes'])]
    # List of existing allocations on those nodes
    node_allocs = [list() for node in nodes]
    for task_name in tasks:
        # Choose a node randomly
        node_i = random.randint(0, len(nodes) - 1)
        node_allocs[node_i].append(task_name)
        schedule[task_name] = {
            # The time slot is based on how many nodes are already scheduled on this "node"
            'time_slot': len(node_allocs[node_i]) - 1,
            'resource': nodes[node_i],
        }
        log.info('Scheduling %s on %s at time slot %i'
                 % (task_name, schedule[task_name]['resource'],
                    schedule[task_name]['time_slot']))
    return schedule
