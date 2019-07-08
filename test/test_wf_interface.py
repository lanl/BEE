#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

import unittest

import beeflow.common.wf_interface as wf_interface


class WFInterfaceTest(unittest.TestCase):
    """Unit test case for the workflow interface."""

    def test_create_task(self):
        """Test task creation."""
        task_id = "test"
        task_name = "Test Task"
        base_command = "ls"
        arguments = ["-a", "-l", "-F"]
        dependencies = {"dependency1", "dependency2", "dependency3"}
        requirements = {"foo.txt", "bar.hl"}

        task = wf_interface.create_task(
            task_id=task_id,
            name=task_name,
            base_command=base_command,
            arguments=arguments,
            dependencies=dependencies,
            requirements=requirements)

        self.assertEqual(task_id, task.id)
        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertListEqual(arguments, task.arguments)
        self.assertSetEqual(dependencies, task.dependencies)
        self.assertEqual(requirements, task.requirements)

    def test_create_workflow(self):
        """Test workflow creation and insertion into the Neo4j database."""
        tasks = []
        tasks.append(wf_interface.create_task("prep", "Data Prep", "ls"))
        tasks.append(wf_interface.create_task(
            "crank0", "Compute 0", "rm", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
            "crank1", "Compute 1", "find", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
            "crank2", "Compute 2", "yes", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
            "viz", "Visualization", "ln", dependencies={"crank0", "crank1", "crank2"}))

        workflow = wf_interface.create_workflow(tasks)
        self.assertListEqual(tasks, workflow.tasks)
        self.assertIsNone(workflow.outputs)
        self.assertSetEqual({tasks[0]}, workflow.head_tasks)

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
