"""
MARS Training program for BEE.

Implementation of the MARS training algorithm for BEE.
"""
import numpy as np
import tensorflow as tf
import os
import json
import sys
import time
import os.path as osp
import beeflow.scheduler.mars as mars


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workload', type=str,
                        default='./schedule_log.txt')
    # parser.add_argument('--model', type=str, default='./model/model.txt')
    parser.add_argument('--gamma', type=float, default=1)
    parser.add_argument('--seed', '-s', type=int, default=0)
    parser.add_argument('--cpu', type=int, default=1)
    parser.add_argument('--trajs', type=int, default=100)
    parser.add_argument('--epochs', type=int, default=4000)
    parser.add_argument('--exp_name', type=str, default='mars')
    parser.add_argument('--pre_trained', type=int, default=0)
    parser.add_argument('--trained_model', type=str,
                        default='./model')
    parser.add_argument('--attn', type=int, default=0)
    parser.add_argument('--shuffle', type=int, default=0)
    parser.add_argument('--backfil', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--score_type', type=int, default=0)
    parser.add_argument('--batch_job_slice', type=int, default=0)
    args = parser.parse_args()

    if args.pre_trained:
        # TODO: pre_trained is not working yet
        actor, critic = mars.load_models('model')
    else:
        actor = mars.ActorModel()
        critic = mars.CriticModel()
    # TODO: Use hyper-parameters
    workload = mars.Workload.load(args.workload)
    for record in workload.records:
        # TODO
        record = tf.constant([record])
        # Learn
        with tf.GradientTape() as tape1, tf.GradientTape() as tape2:
            p = actor.call(record)
            # Calculate the action index
            pl = [float(n) for n in p[0]]
            a = pl.index(max(pl))
            # TODO: Temporary loss calculation
            actor_loss = -np.log(pl[a] / sum(pl))
            # TODO: Should the critic use the result of the actor?
            v = critic.call(record)
            # TODO: Calculate next state critic value
            # TODO: Add in gamma and reward here
            # TODO: Calculate proper reward here
            reward = 1.0
            critic_loss = reward - v
        # Do the update
        actor_grads = tape1.gradient(p, actor.trainable_variables)
        critic_grads = tape2.gradient(v, critic.trainable_variables)
        actor_opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        critic_opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        actor_opt.apply_gradients(zip(actor_grads, actor.trainable_variables))
        critic_opt.apply_gradients(zip(critic_grads, critic.trainable_variables))

    # For some reason predict() must be run on the actor and critic before they
    # can be saved. See https://github.com/tensorflow/tensorflow/issues/31057
    record = tf.constant([workload.records[0]])
    actor.predict(record)
    critic.predict(record)
    mars.save_models(actor, critic, args.trained_model)
