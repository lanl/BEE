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
import beeflow.scheduler.evaluate as evaluate
import beeflow.scheduler.sched_types as sched_types


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--workload', type=str,
                        default='./schedule_log.txt')
    parser.add_argument('--step-size', type=int, default=10, dest='step_size',
                        help=('step size to use for training (number of tasks '
                              'to pass at once)'))

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
    # workload = mars.Workload.load(args.workload)
    workload = evaluate.read_logfile(args.workload)
    workload = [sched_types.Task.decode(task) for task in workload]
    buf = []
    # for record in workload.records:
    for i in range(0, len(workload), args.step_size):
        # record = tf.constant([record])
        tasks = workload[i:i+args.step_size]
        # Learn
        with tf.GradientTape() as tape1, tf.GradientTape() as tape2:
            ps = []
            vs = []
            actor_losses = []
            critic_losses = []
            for task in tasks:
                vec = tf.constant([mars.workflow2vec(task, tasks)])
                print(vec)
                p = actor.call(vec)
                ps.append(p)
                # Calculate the action index
                pl = [float(n) for n in p[0]]
                a = pl.index(max(pl))
                # TODO: Add gamma
                reward = 1.0 if a not in buf else 0.2

                # Empty the buffer if necessary
                if len(buf) == 10:
                    buf.clear()
                buf.append(a)

                # TODO: Temporary loss calculation
                # TODO: Should the critic use the result of the actor?
                # TODO: Calculate next state critic value
                actor_losses.append(-np.log(pl[a] / sum(pl)))
                v = critic.call(vec)
                vs.append(v)
                critic_losses.append(reward - v)

            # TODO: Average losses
            actor_loss = sum(actor_losses) / len(tasks)
            critic_loss = sum(critic_losses) / len(tasks)
            p = sum(ps) / len(tasks)
            v = sum(vs) / len(tasks)

        # Do the update
        # TODO: Should p and v be used here? Maybe losses, as calculated above,
        # should be here instead
        actor_grads = tape1.gradient(p, actor.trainable_variables)
        critic_grads = tape2.gradient(v, critic.trainable_variables)
        actor_opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        critic_opt = tf.keras.optimizers.Adam(learning_rate=0.01)
        actor_opt.apply_gradients(zip(actor_grads, actor.trainable_variables))
        critic_opt.apply_gradients(zip(critic_grads, critic.trainable_variables))

    # For some reason predict() must be run on the actor and critic before they
    # can be saved. See https://github.com/tensorflow/tensorflow/issues/31057
    vec = tf.constant([mars.workflow2vec(workload[0], workload[:args.step_size])])
    # record = tf.constant([workload.records[0]])
    actor.predict(vec)
    critic.predict(vec)
    mars.save_models(actor, critic, args.trained_model)
