# Scheduler

This directory contains the initial scheduler implementation with a REST
API and tests.

- `test-scheduler-api.sh` - test the scheduler REST API
    - `python scheduler.py` must be run in a separate terminal
- `test_allocation.py` - unit tests of the allocation part of the scheduler

## Design notes

In order to represent dependencies between tasks when passing workflows to the
scheduler, the steps of a workflow need to be broken down into a list of lists
of tasks. In other words, at each index of the list there must be a list of
indepedent tasks that can be run in parallel without causing problems.

See the example below where there are four different tasks. `task0` must be run
first, then `task1` and `task2` can run in parallel and finally `task3` can run
after `task1` and `task2` have completed.

```
     |task0|
       / \
      /   \
     /     \
 |task1| |task2|
    \      /
     \    /
      \  /
    |task3|

[[task0],
 [task1, task2],
 [task3]]
```
