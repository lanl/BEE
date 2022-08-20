"""Test internal MARS functions."""
import os
import tensorflow as tf

from beeflow.scheduler import mars_util
from beeflow.scheduler import mars
from beeflow.scheduler import task


def test_workflow2vec_one_task():
    """Test workflow2vec() with one task."""
    tasks = [task.Task(workflow_name='workflow-1', task_name='task-1',
             requirements={'cost': 3.0, 'max_runtime': 2})]

    vec = mars_util.workflow2vec(tasks[0], tasks)

    # TODO: Assert correct size and contains task
    assert len(vec) == mars_util.VECTOR_SIZE
    assert vec[0] == 3.0
    assert vec[1] == 2.0
    assert all(v == 0.0 for v in vec[2:])


def test_workflow2vec_three_tasks():
    """Test workflow2vec() with three tasks."""
    tasks = [
        task.Task(workflow_name='workflow-1', task_name='task-1',
                  requirements={'cost': 3.0, 'max_runtime': 4}),
        task.Task(workflow_name='workflow-1', task_name='task-2',
                  requirements={'cost': 44.0, 'max_runtime': 1}),
        task.Task(workflow_name='workflow-1', task_name='task-3',
                  requirements={'cost': -10.0, 'max_runtime': 55})
    ]

    vec = mars_util.workflow2vec(tasks[1], tasks)

    # TODO: Assert correct size and contains task information of all three
    # tasks
    assert len(vec) == mars_util.VECTOR_SIZE
    assert vec[0] == 44.0
    assert vec[1] == 1.0
    assert vec[2] == 3.0
    assert vec[3] == 4.0
    assert vec[4] == -10.0
    assert vec[5] == 55.0
    assert all(v == 0.0 for v in vec[6:])
    # assert vec == []


def test_model_default():
    """Test saving a default model."""
    # TODO: Choose a truly temporary filename
    fname = '/tmp/test-model'

    model_old = mars.Model()
    model_old.save(fname)
    model_new = mars.Model.load(fname)

    assert (tf.math.equal(layer_a, layer_b)
            for layer_a, layer_b in zip(model_old.layers, model_new.layers))
    os.remove(fname)


# def test_build_availability_list():
#    """Test build_availability_list() with one task and no resources.
#
#    Test build_availability_list() with one task and no resources.
#    """
#    tasks = [sched_types.Task(workflow_name='workflow-1', task_name='task-1',
#                              requirements={'cost': 33.0, 'max_runtime': 44})]
#
#    assert mars.build_availability_list(tasks, tasks[0], []) == []

# TODO: Add more tests for test_build_availability_list()
# Ignore W0511: This is related to issue #333
# pylama:ignore=W0511
