"""MARS Utility Functions and Parameters."""

VECTOR_SIZE = 512


def workflow2vec(task, tasks):
    """Convert a workflow with a particular into a vector representation.

    Represent a workflow with a particular task as a vector and return it.
    :param task: task being scheduled
    :type task: instance of Task
    :param tasks: list of indepdent workflow tasks
    :type tasks: list of instance of Task
    """
    # Note: task must be in the list of tasksjj
    i = tasks.index(task)
    new_tasks = tasks[:i]
    new_tasks.extend(tasks[i + 1:])
    tasks = new_tasks
    vec = _task2vec(task)
    # vec = [float(t.requirements.cost), float(t.requirements.max_runtime)]
    for t in tasks:
        vec.extend(_task2vec(t))
        # vec.extend([float(task.requirements.cost),
        #            float(task.requirements.max_runtime)])
    # Resize the vector
    if len(vec) < VECTOR_SIZE:
        vec.extend([0.0] * (VECTOR_SIZE - len(vec)))
    elif len(vec) > VECTOR_SIZE:
        vec = vec[:VECTOR_SIZE]
    return vec


def _task2vec(task):
    """Convert a single task into a vector.

    Convert a single task into a vector and return it.
    :param task: task to be converted into a vector
    :type task: instance of Task
    """
    # TODO: Add more than just two features later
    return [
        float(task.requirements.cost),
        float(task.requirements.max_runtime),
    ]
# Ignore W0511: This is related to issue #333.
# pylama:ignore=W0511
