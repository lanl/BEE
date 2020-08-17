"""MARS RL implementation.
"""
import json
import numpy as np
import tensorflow as tf

import beeflow.scheduler.util as util

# TODO: Perhaps this should be set in the config
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
    new_tasks.extend(tasks[i+1:])
    tasks = new_tasks
    vec = _task2vec(task)
    # vec = [float(t.requirements.cost), float(t.requirements.max_runtime)]
    for task in tasks:
        vec.extend(_task2vec(task))
        # vec.extend([float(task.requirements.cost),
        #            float(task.requirements.max_runtime)])
    # Resize the vector
    if len(vec) < VECTOR_SIZE:
        vec.extend([0.0] * (VECTOR_SIZE - len(vec)))
    elif len(vec) > VECTOR_SIZE:
        vec = vec[:VECTOR_SIZE]
    return vec


class Workload:
    """Workload class.

    Class for loading a saved workload.
    """

    def __init__(self, records):
        """Workload constructor.

        Workload constructor.
        """
        self.records = records

    @staticmethod
    def load(fname):
        """Load the workload from a file and return it.

        Load the workload from a file and return it.
        :param fname: file name
        :type fname: str
        """
        with open(fname) as fp:
            records = []
            for line in fp:
                records.append([float(f) for f in line.split()])
            return Workload(records)


class Model:
    """Model for MARS.

    Model for MARS.
    """

    # TODO
    def __init__(self, layers=None):
        """Constructor for MARS.

        Constructor for MARS.
        """
        # TODO: Determine the best number of layers
        if layers is not None:
            self.layers = layers
        else:
            self.layers = [
                tf.random.uniform((VECTOR_SIZE, 64)),
                tf.random.uniform((64, 64)),
                tf.random.uniform((64, 64)),
                tf.random.uniform((64, 64)),
            ]

    def policy(self, vec, total_avail):
        """Calculate the policy.

        Calculate the policy.
        :param vec: Input state vector
        :type vec: list of int
        :param total_avail: Number of resources+time slots available
        :type total_avail: int
        :rtype: index of resource to allocate (i >= 0 and i < total_avail)
        """
        vec = tf.reshape(vec, (1, VECTOR_SIZE))
        # TODO: Convert this into the actual model policy function
        if not total_avail:
            return -1, None
        x = vec
        params = []
        for layer in self.layers:
            params.append(x)
            x = tf.matmul(x, layer)
        # Calculate the action
        mean = tf.math.reduce_mean(x)
        total = tf.math.reduce_sum(x)
        a = int(mean / total) * (total_avail - 1)
        return a, params, x

    def make_batch(self, cost, result, params):
        """Make the batch for this expected value.

        Based on the cost of the expected value calculate a list of
        update tensors that can be used to update the layers and
        return it.
        """
        # Calculate the cost for the expected value then return a
        # list of tensors 
        # TODO: This just returns zero tensors
        # return [tf.zeros(layer.shape) for layer in self.layers]
        batch = []
        indices = list(range(len(self.layers)))
        indices.reverse()
        # tmp is being used during backpropagation
        # TODO: Cost may not be used correctly
        tmp = result * cost
        for i in indices:
            # TODO: This isn't exactly right
            update = tf.matmul(params[i].numpy().T, tmp)
            assert update.shape == self.layers[i].shape
            batch.append(update)
            tmp = params[i]
        # Reverse it for a later update
        batch.reverse()
        return batch

    def calculate_update(self, minibatch):
        """Calculate the update to do for the minibatch.

        Calculate the update for the minibatch.
        :param minibatch:
        :type minibatch:
        """
        # Initialize the total_update list to zero tensors matching
        # the size of the layers
        total_update = [tf.zeros(layer.shape) for layer in self.layers]
        count = float(len(minibatch))
        # Total the values of the tensors in each update of the minibatch
        for update in minibatch:
            for i, total in enumerate(total_update):
                print(total.shape, update[i].shape)
                total_update[i] = total + update[i]
        # Averate the total tensor
        return [total / count for total in total_update]

    def apply_update(self, update):
        """Apply an update.

        Apply an update to the layers of the model.
        :param update: update list for each layer
        :type update: list of instance of tf.Tensor
        """
        for i, layer in enumerate(self.layers):
            self.layers[i] = layer - update[i]

    @staticmethod
    def load(fname):
        """Load the model and return it.

        Load the model and return it.
        :param fname: file name
        :type fname: str
        """
        # TODO
        with open(fname) as fp:
            layers = json.load(fp)
        layers = [tf.convert_to_tensor(layer) for layer in layers]
        return Model(layers)

    def save(self, fname):
        """Save the model to a file.

        Save the model to a file.
        :param fname: file name
        :type fname: str
        """
        # TODO: Convert layers to a plain Python format
        def layers2list(layers):
            """Convert a layer into a list.

            Convert a layer (or tf.Tensor) into a list.
            """
            try:
                return [layers2list(layer) for layer in layers]
            except TypeError: # Not iterable
                return float(layers)
        layers = layers2list(self.layers)
        with open(fname, 'w') as fp:
            json.dump(layers, fp=fp)


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
