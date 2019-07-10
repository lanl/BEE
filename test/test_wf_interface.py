#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

import unittest

import beeflow.common.wf_interface as wf_interface


class TestWFInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Connect to the Neo4j database."""

    @classmethod
    def tearDownClass(cls):
        """Close the connection to the Neo4j database."""

    def tearDown(self):
        """Clear all data in the Neo4j database."""

    def test_create_task(self):
        """Test task creation."""
        task_name = "Test Task"
        base_command = "ls"
        arguments = ["-a", "-l", "-F"]
        dependencies = {"dependency1", "dependency2", "dependency3"}
        requirements = {"foo.txt", "bar.hl"}

        task = wf_interface.create_task(
            name=task_name,
            base_command=base_command,
            arguments=arguments,
            dependencies=dependencies,
            requirements=requirements)

        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertListEqual(arguments, task.arguments)
        self.assertSetEqual(dependencies, task.dependencies)
        self.assertEqual(requirements, task.requirements)

    def test_create_workflow(self):
        """Test workflow creation and insertion into the Neo4j database."""
        tasks = [
            wf_interface.create_task("Data Prep", "ls", arguments=["-a", "-l", "-F"]),
            wf_interface.create_task("Compute 0", "rm", dependencies={"Data Prep"}),
            wf_interface.create_task("Compute 1", "find", dependencies={"Data Prep"}),
            wf_interface.create_task("Compute 2", "yes", dependencies={"Data Prep"}),
            wf_interface.create_task("Visualization", "ln", arguments=["-s"],
                                     dependencies={"Compute 0", "Compute 1", "Compute 2"})
        ]

        # Workflow assertions
        workflow = wf_interface.create_workflow(tasks)
        self.assertListEqual(tasks, workflow.tasks)
        self.assertIsNone(workflow.outputs)
        self.assertSetEqual({tasks[0]}, workflow.head_tasks)

        # Task assertions
        for task in tasks:
            self.assertIsInstance(task.id, int)

    def test_initialize_workflows(self):
        """Test workflow initialization.

        All head tasks should have their status set from "WAITING" to "READY"
        """

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""

    def test_get_subworkflow(self):
        """Test obtaining of a sub-workflow."""

    def test_finalize_workflows(self):
        """Test workflow finalization."""


if __name__ == "__main__":
    unittest.main()
