# Scheduler

This directory contains the initial scheduler implementation which will
connect to the other BEE components through a REST API.

- `scheduler.py` - REST API code
- `sched_types.py` - Task, workflow and resource representation code
- `allocation.py` - Base scheduling code
- `algorithms.py` - Code implementing the various scheduling algorithms

The scheduler is currently designed to allow for scheduling one set of
independent tasks at a time. So if a first set of tasks must run before a
second set of tasks, then that first set must be scheduled first. When the
first set of tasks has been scheduled and the tasks have completed, then the
second set of tasks may be scheduled to run.

Each task can have a dict of requirements which specify the resources
that they need to run on. Supported requirement values, right now, are:

- `max_runtime` - `int`
- `cores` - `int`
