"""MARS RL implementation."""
import json
import os
import tensorflow as tf

from beeflow.scheduler import mars_util


def _get_action(x, total_avail):
    """Get the action for x.

    Get the action for x.
    :param x: tensor to calculate the action from
    :type x: tf.Tensor
    """
    actions = list(x[0].numpy())
    return actions.index(max(actions)) / float(len(actions) - 1) * (total_avail - 1)


class Model:
    """Model for MARS."""

    def __init__(self, layers=None):
        """Construct the MARS object."""
        # TODO: Determine the best number of layers
        if layers is not None:
            self.layers = layers
        else:
            self.layers = [
                tf.random.uniform((mars_util.VECTOR_SIZE, 64)),
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
        vec = tf.reshape(vec, (1, mars_util.VECTOR_SIZE))
        # TODO: Convert this into the actual model policy function
        if not total_avail:
            return -1, None
        x = vec
        params = []
        for layer in self.layers:
            params.append(x)
            x = tf.matmul(x, layer)
        # Calculate the action
        action = _get_action(x, total_avail)
        return action, params, x

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
        with open(fname, encoding='utf-8') as fp:
            layers = json.load(fp)
        layers = [tf.convert_to_tensor(layer) for layer in layers]
        return Model(layers)

    def save(self, fname):
        """Save the model to a file.

        Save the model to a file.
        :param fname: file name
        :type fname: str
        """
        # Convert layers to a plain Python format
        layers = [[[float(n) for n in tensor] for tensor in layer]
                  for layer in self.layers]
        print(layers)
        with open(fname, 'w', encoding='utf-8') as fp:
            json.dump(layers, fp=fp)


# Actor-Critic Example based on
# https://towardsdatascience.com/actor-critic-with-tensorflow-2-x-part-1-of-2-d1e26a54ce97

class ModelBase(tf.keras.Model):
    """Model base class.

    Model base class.
    """

    def __init__(self, layers=None):
        """Model base constructor.

        Model base constructor.
        """
        super().__init__()
        self._layers = [] if layers is None else layers

    @tf.function
    def call(self, data):
        """Call the critic for a value.

        Call the critic for a value.
        """
        x = data
        for layer in self._layers:
            x = layer(x)
        return x


class CriticModel(ModelBase):
    """The Critic class.

    The Critic class.
    """

    def __init__(self):
        """Critic constructor.

        Critic constructor.
        """
        super().__init__(layers=[
            tf.keras.layers.Dense(2048, activation='relu'),
            tf.keras.layers.Dense(1560, activation='relu'),
            tf.keras.layers.Dense(1, activation=None),
        ])


class ActorModel(ModelBase):
    """Actor model class.

    Actor model class.
    """

    def __init__(self):
        """Actor model constructor.

        Actor model constructor.
        """
        super().__init__(layers=[
            tf.keras.layers.Dense(2048, activation='relu'),
            tf.keras.layers.Dense(1560, activation='relu'),
            tf.keras.layers.Dense(4, activation='softmax'),
        ])


def load_models(path):
    """Load the models.

    Load the models.
    :rtype: instance of ActorModel, instance of CriticModel
    """
    actor_path = os.path.join(path, 'actor')
    critic_path = os.path.join(path, 'critic')
    actor = tf.keras.models.load_model(actor_path)
    critic = tf.keras.models.load_model(critic_path)
    return actor, critic


def save_models(actor, critic, path):
    """Save the models.

    Save the models.
    """
    if not os.path.exists(path):
        os.mkdir(path)
    actor_path = os.path.join(path, 'actor')
    critic_path = os.path.join(path, 'critic')
    actor.save(actor_path)
    critic.save(critic_path)


def task2vec(task):
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
# Ignore W0511: This relates to issue #333
# pylama:ignore=W0511
