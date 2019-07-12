#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

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
        subworkflow = "Subworkflow 1"

        task = wf_interface.create_task(
            name=task_name,
            base_command=base_command,
            arguments=arguments,
            dependencies=dependencies,
            subworkflow=subworkflow)

        # Task assertions
        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertListEqual(arguments, task.arguments)
        self.assertSetEqual(dependencies, task.dependencies)
        self.assertEqual(subworkflow, task.subworkflow)

    def test_create_workflow(self):
        """Test workflow creation."""
        tasks = _create_test_tasks()

        # Workflow assertions
        workflow = wf_interface.create_workflow(tasks)
        self.assertSetEqual(set(tasks), workflow.tasks)
        self.assertIsNone(workflow.requirements)
        self.assertIsNone(workflow.outputs)

        # Task assertions
        for task_id, task in enumerate(tasks):
            self.assertEqual(task_id, task.id)

    def test_load_workflow(self):
        """Test workflow insertion into the graph database."""
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)

        # Test workflow loading
        wf_interface.load_workflow(workflow)

        # TODO: test that the workflow is actually loaded

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        tasks = _create_test_tasks()
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

        All head tasks should have their status set from "WAITING" to "READY"
        """
        tasks = _create_test_tasks()

        wf_interface.create_workflow(tasks)
        wf_interface.initialize_workflow()

        self.assertEqual("READY", wf_interface.get_task_state(tasks[0]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[1]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[2]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[3]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[4]))

    def test_run_workflow(self):
        """Test workflow running."""

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""

    def test_get_task_state(self):
        """Test obtaining of task status."""

    def test_finalize_workflow(self):
        """Test workflow finalization."""


def _create_test_tasks():
    """Create test tasks to reduce redundancy."""
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
