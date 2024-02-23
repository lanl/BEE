"""Container build utility code."""
import jsonpickle


def arg2task(task_arg):
    """Convert JSON encoded task to Task object.

    The build driver will expect a Task object, and the build
    interface starts with a JSON representation of the Task object.
    """
    return jsonpickle.decode(task_arg)


def task2arg(task):
    """Convert Task object to JSON encoded string.

    The build interface needs to pass Task data on the command line,
    because each compute node needs to understand the Task description.
    JSON format is a convenient way to describe the Task object at the
    command line.
    """
    return jsonpickle.encode(task)


class ContainerBuildError(Exception):
    """Cotnainer build error class."""
