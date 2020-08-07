import numpy as np
import tensorflow as tf
import os
import json
import sys
import time
import os.path as osp

import beeflow.scheduler.mars as mars


def load_model(trained_model):
    """Load the trained model.

    Load the trained model.
    :param trained_model: model dir name 
    :type trained_model: str
    :rtype: instance of tf.keras.Model
    """
    with open(trained_model) as fp:
        data = json.load(fp)
    return [tf.constant(l) for l in data]

def save_model(layers, fname):
    """Save the model to a file.

    Save the model to a file.
    :param layers: model to save:
    :type layers:
    :param fname: file name
    :type fname: str
    """
    # TODO
    def construct(elem):
        try:
            return [construct(e) for e in elem]
        except TypeError:
            return float(elem)
    data = construct(layers)
    with open(fname, 'w') as fp:
        json.dump(data, fp=fp)
    # tf.keras.models.save_model(model, fname)


def policy_loader(model_path, itr='last'):
    if itr == 'last':
        saves = [int(x[11:]) for x in os.listdir(model_path) if 'simple_save' in x and len(x) > 11]
        itr = '%d' % max(saves) if len(saves) > 0 else ''
    else:
        itr = '%d' % itr
    sess = tf.Session()
    model = restore_tf_graph(sess, osp.join(model_path, 'simple_save' + itr))
    pi = model['pi']
    v = model['v']
    get_probs = lambda x, y: sess.run(pi, feed_dict={model['x']: x.reshape(-1, MAX_QUEUE_SIZE * TASK_FEATURES),
                                                     model['mask']: y.reshape(-1, MAX_QUEUE_SIZE)})
    get_v = lambda x: sess.run(v, feed_dict={model['x']: x.reshape(-1, MAX_QUEUE_SIZE * TASK_FEATURES)})
    from spinup.utils.run_utils import setup_logger_kwargs
    return get_probs, get_v

def mlp3(x, act_dim):
    x = tf.reshape(x, shape=[-1, MAX_QUEUE_SIZE, TASK_FEATURES])
    x = tf.layers.dense(x, units=32, activation=tf.nn.relu)
    x = tf.layers.dense(x, units=16, activation=tf.nn.relu)
    x = tf.layers.dense(x, units=8, activation=tf.nn.relu)
    x = tf.squeeze(tf.layers.dense(x, units=1), axis=-1)
    x = tf.layers.dense(x, units=64, activation=tf.nn.relu)
    x = tf.layers.dense(x, units=32, activation=tf.nn.relu)
    x = tf.layers.dense(x, units=8, activation=tf.nn.relu)
    return tf.layers.dense(x, units=act_dim)

def attention(x, act_dim):
    x = tf.reshape(x, shape=[-1, MAX_QUEUE_SIZE, TASK_FEATURES])
    q = tf.layers.dense(x, units=32, activation=tf.nn.relu)
    k = tf.layers.dense(x, units=32, activation=tf.nn.relu)
    v = tf.layers.dense(x, units=32, activation=tf.nn.relu)
    score = tf.matmul(q, tf.transpose(k, [0, 2, 1]))
    score = tf.nn.softmax(score, -1)
    attn = tf.reshape(score, (-1, MAX_QUEUE_SIZE, MAX_QUEUE_SIZE))
    x = tf.matmul(attn, v)
    x = tf.layers.dense(x, units=16, activation=tf.nn.relu)

    x = tf.layers.dense(x, units=8, activation=tf.nn.relu)
    x = tf.squeeze(tf.layers.dense(x, units=1), axis=-1)
    return x


def lenet(x_ph, act_dim):
    m = int(np.sqrt(MAX_QUEUE_SIZE))
    x = tf.reshape(x_ph, shape=[-1, m, m, TASK_FEATURES])
    x = tf.layers.conv2d(inputs=x, filters=32, kernel_size=[1, 1], strides=1)
    x = tf.layers.max_pooling2d(x, [2, 2], 2)
    x = tf.layers.conv2d(inputs=x, filters=64, kernel_size=[1, 1], strides=1)
    x = tf.layers.max_pooling2d(x, [2, 2], 2)
    x = tf.layers.flatten(x)
    x = tf.layers.dense(x, units=64)

    return tf.layers.dense(
        inputs=x,
        units=act_dim,
        activation=None
    )

def categorical_policy(x, a, mask, action_space, attn):



    act_dim = action_space.n
    if attn:
        output_layer = attention(x, act_dim)
    else:
        output_layer = lenet(x, act_dim)
    output_layer = output_layer + (mask - 1) * 1000000
    logp_all = tf.nn.log_softmax(output_layer)

    pi = tf.squeeze(tf.multinomial(output_layer, 1), axis=1)
    logp = tf.reduce_sum(tf.one_hot(a, depth=act_dim) * logp_all, axis=1)
    logp_pi = tf.reduce_sum(tf.one_hot(pi, depth=act_dim) * logp_all, axis=1)
    return pi, logp, logp_pi, output_layer

def actor_critic(x, a, mask, action_space=None, attn=False):




    with tf.variable_scope('pi'):
        pi, logp, logp_pi, out = categorical_policy(x, a, mask, action_space, attn)
    with tf.variable_scope('v'):
        v = tf.squeeze(mlp3(x, 1), axis=1)
    return pi, logp, logp_pi, v, out


class MARSBuffer:

    def __init__(self, obs_dim, act_dim, size, gamma=0.99, lam=0.95):
        size = size * 100
        self.obs_buf = np.zeros(combined_shape(size, obs_dim), dtype=np.float32)
        self.cobs_buf = None
        self.act_buf = np.zeros(combined_shape(size, act_dim), dtype=np.float32)
        self.mask_buf = np.zeros(combined_shape(size, MAX_QUEUE_SIZE), dtype=np.float32)
        self.adv_buf = np.zeros(size, dtype=np.float32)
        self.rew_buf = np.zeros(size, dtype=np.float32)
        self.ret_buf = np.zeros(size, dtype=np.float32)
        self.val_buf = np.zeros(size, dtype=np.float32)
        self.logp_buf = np.zeros(size, dtype=np.float32)
        self.gamma, self.lam = gamma, lam
        self.ptr, self.path_start_idx, self.max_size = 0, 0, size

    def store(self, obs, cobs, act, mask, rew, val, logp):
        assert self.ptr < self.max_size  # buffer has to have room so you can store
        self.obs_buf[self.ptr] = obs
        self.act_buf[self.ptr] = act
        self.mask_buf[self.ptr] = mask
        self.rew_buf[self.ptr] = rew
        self.val_buf[self.ptr] = val
        self.logp_buf[self.ptr] = logp
        self.ptr += 1

    def finish_path(self, last_val=0):
        path_slice = slice(self.path_start_idx, self.ptr)
        rews = np.append(self.rew_buf[path_slice], last_val)
        vals = np.append(self.val_buf[path_slice], last_val)
        deltas = rews[:-1] + self.gamma * vals[1:] - vals[:-1]
        self.adv_buf[path_slice] = discount_cumsum(deltas, self.gamma * self.lam)
        self.ret_buf[path_slice] = discount_cumsum(rews, self.gamma)[:-1]
        self.path_start_idx = self.ptr

    def get(self):
        assert self.ptr < self.max_size
        actual_size = self.ptr
        self.ptr, self.path_start_idx = 0, 0
        actual_adv_buf = np.array(self.adv_buf, dtype=np.float32)
        actual_adv_buf = actual_adv_buf[:actual_size]
        adv_sum = np.sum(actual_adv_buf)
        adv_n = len(actual_adv_buf)
        adv_mean = adv_sum / adv_n
        adv_sum_sq = np.sum((actual_adv_buf - adv_mean) ** 2)
        adv_std = np.sqrt(adv_sum_sq / adv_n)
        actual_adv_buf = (actual_adv_buf - adv_mean) / adv_std
        return [self.obs_buf[:actual_size], self.act_buf[:actual_size], self.mask_buf[:actual_size], actual_adv_buf,
                self.ret_buf[:actual_size], self.logp_buf[:actual_size]]

    @property
    def size(self):
        return self.ptr


def categorical_policy(x, mlp_layers):
    with tf.GradientTape() as g:
        # Compute the loss
        for layer in mlp_layers:
            # Note: https://github.com/tensorflow/tensorflow/issues/29942
            g.watch(layer)
            x = tf.maximum(0, tf.matmul(x, layer))
        loss = tf.reduce_mean(x)
    grads = g.gradient(x, mlp_layers)
    # Do the update
    for i, (grad, layer) in enumerate(zip(grads, mlp_layers)):
        print(grad)
        mlp_layers[i] = layer + loss * grad
    pi = x
    logp_all = tf.nn.log_softmax(x)
    # pi = tf.squeeze(tf.multinomial(x, 1), axis=1)
    # logp_pi = tf.reduce_sum(pi * logp_all, axis=1)
    return pi, logp_all

def critic(pi, mlp_layers, in_dim):
    # Convert pi into the correct input format
    pi = [[float(val) for val in p][:in_dim] for p in pi]
    pi = [(p + [0.0] * (in_dim - len(p))) if len(p) < in_dim else p for p in pi]
    x = tf.constant(pi)
    with tf.GradientTape() as g:
        # Compute the loss
        for layer in mlp_layers:
            # Note: https://github.com/tensorflow/tensorflow/issues/29942
            g.watch(layer)
            x = tf.maximum(0, tf.matmul(x, layer))
        loss = tf.reduce_mean(x)
    grads = g.gradient(x, mlp_layers)
    # Do the update
    for i, (grad, layer) in enumerate(zip(grads, mlp_layers)):
        mlp_layers[i] = layer + loss * grad
    return x


class Model:
    """MARS model.

    MARS model.
    """

    def __init__(self, in_dim, act_dim):
        """Constructor for the MARS model.

        Constructor for the MARS model.
        :param in_dim:
        :type in_dim:
        :param act_dim:
        :type act_dim:
        """
        # TODO
        self.layers = [
            tf.random.uniform((in_dim, 64)),
            tf.random.uniform((64, 64)),
            tf.random.uniform((64, act_dim))
        ]
        # Stored gradients
        self.grads = []
        self.pis = []
        self.rs = []

    def step_train(self, state):
        """Train on one particular state.

        Train on one particular state.
        :param state: input state
        :type state: vector representing the current state
        """
        # TODO

    def actor_critic(self, state):
        """Actor critic algorithm.

        Actor critic algorithm.
        """
        # TODO
        # Calculate the policy
        pi = self.policy(state, g)
        # Calculate the reward
        r = self.reward(pi, g)
        # Store the value
        self.store(pi, r)
        return pi, r

    def store(self, pi, r):
        """Store a result.

        Store a result.
        """
        self.pis.append(pi)
        self.rs.append(r)

def build_model(in_dim, act_dim):
    """Build the model.

    Build the model.
    """
    mlp_layers = [
        tf.random.uniform((in_dim, 64)),
        tf.random.uniform((64, 64)),
        tf.random.uniform((64, act_dim))
    ]
    return mlp_layers

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workload', type=str,
                        default='./schedule_log.txt')
    parser.add_argument('--model', type=str, default='./model/model.txt')
    parser.add_argument('--gamma', type=float, default=1)
    parser.add_argument('--seed', '-s', type=int, default=0)
    parser.add_argument('--cpu', type=int, default=1)
    parser.add_argument('--trajs', type=int, default=100)
    parser.add_argument('--epochs', type=int, default=4000)
    parser.add_argument('--exp_name', type=str, default='mars')
    parser.add_argument('--pre_trained', type=int, default=0)
    parser.add_argument('--trained_model', type=str,
                        default='./output/result_00')
    parser.add_argument('--attn', type=int, default=0)
    parser.add_argument('--shuffle', type=int, default=0)
    parser.add_argument('--backfil', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--score_type', type=int, default=0)
    parser.add_argument('--batch_job_slice', type=int, default=0)
    args = parser.parse_args()

    if args.pre_trained:
        # TODO
        model = mars.Model.load('model')
        # TODO
    else:
        # TODO: Use hyper-parameters
        # workloads, cluster, penalty_task_score = workloads \
        #    .load_workloads(args.workload)
        model = mars.Model()
    
    workload = mars.Workload.load(args.workload)
    for record in workload.records:
        s = record[:-1]
        a_exp = record[-1]
        a, params = model.policy(s, len(s))
        dJ = 2 * (a - a_exp)
        model.apply_gradient(dJ, params, learn_rate=0.01)
    model.save(args.trained_model)
    sys.exit(1)

    workload = mars.Workload.load(args.workload)
    buf = []

    def update(buf, model):
        """Update the model with the buffer.

        Update the model with the passed buffer values.
        :param buf: buffer with train values
        :type buf: list of instance of dict
        :param model: model to update
        :type model: instance of mars.Model
        """
        # TODO: How to reduce mean of buffer
        dJ = tf.reduce_mean([b['dJ'] for b in buf])
        # TODO: Average the params
        factor = 1.0 / len(buf)
        # Initialize the params
        weighted_params = factor * buf[0]['params']
        for params in [b['params'] for b in buf][1:]:
            for i, param in enumerate(params):
                weighted_params[i] += factor * param
        params = weighted_params
        # Apply the average
        model.apply_gradient(dJ, params, learn_rate=0.01)

    for record in workload.records:
        s = record[:-1]
        # Expected action
        a_exp = record[-1]
        a, params = model.policy(record[:-1], record[-1])
        # TODO: Reward function - CPU, cost, memory use, etc.
        dloss = 2 * (a - a_exp)
        # TODO: Calculate dJ
        dJ = dloss
        # Apply the gradient with dJ
        model.apply_gradient(dloss, params, learn_rate=0.01)
        # TODO
        buf.append({
            'dJ': dJ,
            'params': params,
            'a': a,
        })
        if len(buf) == 512:
            update(buf, model)
    if buf:
        # Apply the gradients left
        update(buf, model)
    sys.exit(0)
