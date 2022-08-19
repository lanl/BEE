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

## MARS

The MARS part of the scheduler uses reinforcement learning to schedule tasks.
Before using this algorithm you must have a trained model. The default trained
model is located in `./model` but can be changed in the config file.

To train a model you will need to run `beeflow/scheduler/train.py`. This will
require a schedule log that is produced by running the scheduler on a number
of workflows. If defaults are used, training can be as simple as running
`python beeflow/scheduler/train.py` which will output the model in the
default directory `./model`.

### Evaluation

To evaluate MARS you can run `python beeflow/scheduler/evaluate.py` on a
specific workflow log file. This will output a number of graphs showing a
performance comparison of the MARS scheduler with other algorithms (like FCFS
and Backfill).
