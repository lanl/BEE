"""MARS RL implementation.
"""
import random

import beeflow.scheduler.util as util

# TODO: Perhaps this should be set in the config
VECTOR_SIZE = 512


def workflow2vec(tasks):
    """Convert a workflow into a vector representation.

    Represent a workflow as a vector and return it.
    :param tasks: list of indepdent workflow tasks
    :type tasks: list of instance of Task
    """
    vec = []
    for task in tasks:
        # TODO: Add more than just two features later
        vec.extend([float(task.requirements.cost),
                    float(task.requirements.max_runtime)])
    # Resize the vector
    if len(vec) < VECTOR_SIZE:
        vec.extend([0.0] * (VECTOR_SIZE - len(vec)))
    elif len(vec) > VECTOR_SIZE:
        vec = vec[:VECTOR_SIZE]
    return vec


class Model:
    """Model for MARS.

    Model for MARS.
    """

    # TODO
    def __init__(self):
        """Constructor for MARS.

        Constructor for MARS.
        """
        # TODO
        pass

    def policy(self, vector, output_dims):
        """Calculate the policy.

        Calculate the policy.
        :param vector:
        :type vector:
        :param output_dims:
        :type output_dims:
        """
        # TODO: Convert this into the actual model policy function
        length = len(output_dims)
        return random.randint(0, length - 1) if length > 0 else -1

    @staticmethod
    def load(fname):
        """Load the model and return it.

        Load the model and return it.
        :param fname: file name
        :type fname: str
        """
        # TODO
        return Model()
