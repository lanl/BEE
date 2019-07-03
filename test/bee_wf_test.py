#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

import unittest

import beeflow.common.bee_wf as wf_interface


class WFInterfaceTest(unittest.TestCase):
    """Unit test case for the workflow interface."""

    def test_create_task(self):
        """Test task creation."""
        TASK_ID = "test"
        TASK_NAME = "Test Task"
        BASE_COMMAND = "ls"
        ARGUMENTS = ["-a", "-l", "-F"]
        DEPENDENCIES = {"dependency1", "dependency2", "dependency3"}
        REQUIREMENTS = {"foo.txt", "bar.hl"}

        task = wf_interface.create_task(
            task_id=TASK_ID,
            name=TASK_NAME,
            base_command=BASE_COMMAND,
            arguments=ARGUMENTS,
            dependencies=DEPENDENCIES,
            requirements=REQUIREMENTS)

        self.assertEqual(TASK_ID, task.id)
        self.assertEqual(TASK_NAME, task.name)
        self.assertEqual(BASE_COMMAND, task.base_command)
        self.assertListEqual(ARGUMENTS, task.arguments)
        self.assertSetEqual(DEPENDENCIES, task.dependencies)
        self.assertEqual(REQUIREMENTS, task.requirements)

    def test_create_workflow(self):
        """Test workflow creation and insertion into the Neo4j database."""
        tasks = []
        tasks.append(wf_interface.create_task(
                "prep", "Data Prep", "ls"))
        tasks.append(wf_interface.create_task(
                "crank0", "Compute 0", "rm", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
                "crank1", "Compute 1", "find", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
                "crank2", "Compute 2", "yes", dependencies={"prep"}))
        tasks.append(wf_interface.create_task(
                "viz", "Visualization", "ln",
                dependencies={"crank0", "crank1", "crank2"}))

        # wf_interface.create_workflow(tasks)


if __name__ == "__main__":
    unittest.main()
