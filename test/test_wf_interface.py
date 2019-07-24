#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

import beeflow.common.wf_interface as wf_interface
import beeflow.common.gdb.gdb_interface as gdb_interface


class TestWFInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def tearDownClass(cls):
        """Close the connection to the Neo4j database."""
        gdb_interface._GDB_DRIVER.close()

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        gdb_interface._GDB_DRIVER.cleanup()

    def test_create_task(self):
        """Test task creation."""
        task_name = "Test Task"
        base_command = "ls"
        arguments = ["-a", "-l", "-F"]
        dependencies = {"Dependency 1", "Dependency 2", "Dependency 3"}
        requirements = {"ram": 1024, "cores": 4}
        hints = {"cpus": 2}
        subworkflow = "Test Subworkflow"
        inputs = {"input1.txt", "input2.txt"}
        outputs = {"test_task_done"}

        task = wf_interface.create_task(
            name=task_name,
            base_command=base_command,
            arguments=arguments,
            dependencies=dependencies,
            requirements=requirements,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        # Task assertions
        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertListEqual(arguments, task.arguments)
        self.assertSetEqual(dependencies, task.dependencies)
        self.assertEqual(requirements, task.requirements)
        self.assertEqual(hints, task.hints)
        self.assertEqual(subworkflow, task.subworkflow)
        self.assertEqual(inputs, task.inputs)
        self.assertEqual(outputs, task.outputs)

    def test_create_workflow(self):
        """Test workflow creation.

        Creation of bee_init and bee_exit is manual.
        """
        tasks = _create_test_tasks()
        requirements = {"ranks": 128}
        hints = {"cluster": "badger"}
        inputs = {"inputs.txt"}
        outputs = {"outputs.txt"}

        workflow = wf_interface.create_workflow(
            tasks=tasks,
            requirements=requirements,
            hints=hints,
            inputs=inputs,
            outputs=outputs)

        # Workflow assertions
        self.assertSetEqual(set(tasks), workflow.tasks)
        self.assertEqual(requirements, workflow.requirements)
        self.assertEqual(hints, workflow.hints)
        self.assertEqual(inputs, workflow.inputs)
        self.assertEqual(outputs, workflow.outputs)

        # Task assertions
        for task_id, task in enumerate(tasks):
            self.assertEqual(task_id, task.id)

    def test_load_workflow_automatic(self):
        """Test workflow insertion into the graph database.

        Creation of bee_init and bee_exit is automatic.
        """
        tasks = _create_test_tasks(bee_nodes=False)
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)

        # Test task states
        for task in tasks:
            self.assertEqual("WAITING", wf_interface.get_task_state(task))

    def test_load_workflow_manual(self):
        """Test workflow insertion into the graph database.

        Creation of bee_init and bee_exit is manual.
        """
        tasks = _create_test_tasks()

        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)

        # Test task states
        for task in tasks:
            self.assertEqual("WAITING", wf_interface.get_task_state(task))

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        tasks = _create_test_tasks(bee_nodes=False)
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)

        # Subworkflow assertions
        self.assertEqual(wf_interface.create_workflow(tasks[0:1]),
                         wf_interface.get_subworkflow("Prep"))
        self.assertEqual(wf_interface.create_workflow(tasks[1:4]),
                         wf_interface.get_subworkflow("Compute"))
        self.assertEqual(wf_interface.create_workflow(tasks[4:5]),
                         wf_interface.get_subworkflow("Visualization"))

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The bee_init node should have its state set from "WAITING" to "READY"
        """
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        wf_interface.initialize_workflow()

        self.assertEqual("READY", wf_interface.get_task_state(tasks[0]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[1]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[2]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[3]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[4]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[5]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[6]))

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        tasks = _create_test_tasks(bee_nodes=False)
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        dependent_tasks = wf_interface.get_dependent_tasks(tasks[0])

        self.assertSetEqual(set(tasks[1:4]), dependent_tasks)

    def test_get_task_state(self):
        """Test obtaining of task status."""
        task = wf_interface.create_task("Test Task", "ls")
        workflow = wf_interface.create_workflow([task])
        wf_interface.load_workflow(workflow)

        self.assertEqual("WAITING", wf_interface.get_task_state(task))

    def test_finalize_workflow(self):
        """Test workflow finalization."""
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        wf_interface.finalize_workflow()

        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[0]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[1]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[2]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[3]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[4]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[5]))
        self.assertEqual("READY", wf_interface.get_task_state(tasks[6]))


def _create_test_tasks(bee_nodes=True):
    """Create test tasks to reduce redundancy.

    :param bee_nodes: flag to add bee_init and bee_exit nodes
    :type bee_nodes: boolean
    """
    if bee_nodes:
        tasks = [
            wf_interface.create_task("bee_init"),
            wf_interface.create_task("Data Prep", "ls", arguments=["-a", "-l", "-F"],
                                     dependencies={"bee_init"}, subworkflow="Prep"),
            wf_interface.create_task("Compute 0", "rm", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Compute 1", "find", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Compute 2", "yes", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Visualization", "ln", arguments=["-s"],
                                     dependencies={"Compute 0", "Compute 1", "Compute 2"},
                                     subworkflow="Visualization"),
            wf_interface.create_task("bee_exit", dependencies={"Visualization"})
        ]
    else:
        tasks = [
            wf_interface.create_task("Data Prep", "ls", arguments=["-a", "-l", "-F"],
                                     subworkflow="Prep"),
            wf_interface.create_task("Compute 0", "rm", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Compute 1", "find", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Compute 2", "yes", dependencies={"Data Prep"},
                                     subworkflow="Compute"),
            wf_interface.create_task("Visualization", "ln", arguments=["-s"],
                                     dependencies={"Compute 0", "Compute 1", "Compute 2"},
                                     subworkflow="Visualization")
        ]

    return tasks


if __name__ == "__main__":
    unittest.main()
