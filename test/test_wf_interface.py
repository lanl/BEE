#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest
import warnings

from beeflow.common.wf_interface import WorkflowInterface


class TestWorkflowInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the Workflow interface."""
        warnings.simplefilter('ignore', category=ImportWarning)
        cls.wfi = WorkflowInterface()

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        # if self.wfi.workflow_loaded():
        #     self.wfi.finalize_workflow()

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The bee_init, bee_exit, and metadata nodes should have been created.
        """
        requirements = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024),
                 self.wfi.create_requirement("NetworkAccess", "networkAccess", True)}
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"}, requirements, hints)

        (tasks, requirements, hints) = self.wfi.get_workflow()
        for task in tasks:
            if task.name == "bee_init":
                self.assertEqual(0, task.id)
                self.assertSetEqual({"input.txt"}, task.inputs)
                self.assertSetEqual({"input.txt"}, task.outputs)
            elif task.name == "bee_exit":
                self.assertEqual(1, task.id)
                self.assertSetEqual({"output.txt"}, task.inputs)
                self.assertSetEqual({"output.txt"}, task.outputs)
            else:
                self.fail("BEE init and exit nodes missing")

    def test_execute_workflow(self):
        """Test workflow execution initialization (set bee_init's state to READY)."""
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"})
        self._create_test_tasks()
        self.wfi.execute_workflow()

        bee_init_task = self.wfi.get_task_by_id(0)
        self.assertEqual("READY", self.wfi.get_task_state(bee_init_task))

    def test_finalize_workflow(self):
        """Test workflow deletion from the graph database."""
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"})
        self.wfi.finalize_workflow()

        self.assertFalse(self.wfi.workflow_loaded())

    def test_add_task(self):
        """Test task creation."""
        task_name = "Test Task"
        command = ["ls", "-a", "-l", "-F"]
        hints = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024),
                 self.wfi.create_requirement("NetworkAccess", "networkAccess", True)}
        subworkflow = "Test Subworkflow"
        inputs = {"input.txt"}
        outputs = {"test_task_done"}

        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"test_task_done"})
        task = self.wfi.add_task(
            name=task_name,
            command=command,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        # Task object assertions
        self.assertEqual(task_name, task.name)
        self.assertListEqual(command, task.command)
        self.assertSetEqual(hints, task.hints)
        self.assertEqual(subworkflow, task.subworkflow)
        self.assertSetEqual(inputs, task.inputs)
        self.assertSetEqual(outputs, task.outputs)
        self.assertIsInstance(task.id, int)

        # Graph database assertions
        gdb_task = self.wfi.get_task_by_id(task.id)
        self.assertEqual(gdb_task.name, task.name)
        self.assertListEqual(gdb_task.command, task.command)
        self.assertSetEqual(gdb_task.hints, task.hints)
        self.assertEqual(gdb_task.subworkflow, task.subworkflow)
        self.assertSetEqual(gdb_task.inputs, task.inputs)
        self.assertSetEqual(gdb_task.outputs, task.outputs)
        self.assertEqual(gdb_task.id, task.id)

    def test_create_requirement(self):
        """Test workflow requirement creation."""
        req_class = "ResourceRequirement"
        req_key = "ramMin"
        req_value = 1024

        req = self.wfi.create_requirement(req_class, req_key, req_value)

        self.assertEqual(req_class, req.req_class)
        self.assertEqual(req_key, req.key)
        self.assertEqual(req_value, req.value)

    def test_get_task_by_id(self):
        """Test obtaining a task from the graph database by its ID."""
        task_name = "Test Task"
        command = ["ls", "-a", "-l", "-F"]
        hints = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024),
                 self.wfi.create_requirement("NetworkAccess", "networkAccess", True)}
        subworkflow = "Test Subworkflow"
        inputs = {"input.txt"}
        outputs = {"test_task_done"}

        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"test_task_done"})
        task = self.wfi.add_task(
            name=task_name,
            command=command,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        self.assertEqual(task, self.wfi.get_task_by_id(task.id))

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        requirements = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wfi.create_requirement("NetworkAccess", "networkAccess", True)}
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"}, requirements, hints)
        tasks = self._create_test_tasks()

        self.assertTrue(self.wfi.workflow_loaded())

        (wf_tasks, wf_requirements, wf_hints) = self.wfi.get_workflow()

        self.assertTrue(set(tasks).issubset(wf_tasks))
        self.assertEqual(requirements, wf_requirements)
        self.assertEqual(hints, wf_hints)

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        requirements = {self.wfi.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wfi.create_requirement("NetworkAccess", "networkAccess", True)}
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"}, requirements, hints)
        tasks = self._create_test_tasks()

        # Subworkflow assertion
        (subwf_tasks, subwf_requirements, subwf_hints) = self.wfi.get_subworkflow("Compute")
        self.assertSetEqual(set(tasks[1:4]), subwf_tasks)
        self.assertSetEqual(requirements, subwf_requirements)
        self.assertSetEqual(hints, subwf_hints)

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wfi.get_dependent_tasks(tasks[0])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertSetEqual(set(tasks[1:4]), set(dependent_tasks))

    def test_get_task_state(self):
        """Test obtaining of task status."""
        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")

        # Should be WAITING because workflow not initialized
        self.assertEqual("WAITING", self.wfi.get_task_state(task))

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        # No workflow loaded
        self.assertFalse(self.wfi.workflow_loaded())

        self.wfi.initialize_workflow("TEST", {"input.txt"}, {"output.txt"})

        # Workflow now loaded
        self.assertTrue(self.wfi.workflow_loaded())

    def _create_test_tasks(self):
        """Create test tasks to reduce redundancy.

        :param bee_nodes: flag to add bee_init and bee_exit tasks
        :type bee_nodes: boolean
        """
        # Remember that add_task uploads the task to the database
        tasks = [
            self.wfi.add_task(
                "Data Prep", command=["ls", "-a", "-l", "-F"],
                hints={self.wfi.create_requirement("ResourceRequirement", "ramMax", 2048)},
                inputs={"input.txt"}, outputs={"prep_input.txt"}),
            self.wfi.add_task(
                "Compute 0", command=["rm", "-r", "-f"],
                hints={self.wfi.create_requirement("ResourceRequirement", "ramMax", 2048)},
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output1.txt"}),
            self.wfi.add_task(
                "Compute 1", command=["find"],
                hints={self.wfi.create_requirement("ResourceRequirement", "ramMax", 2048)},
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output2.txt"}),
            self.wfi.add_task(
                "Compute 2", command=["yes"],
                hints={self.wfi.create_requirement("ResourceRequirement", "ramMax", 2048)},
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output3.txt"}),
            self.wfi.add_task(
                "Visualization", command=["ln", "-s"],
                hints={self.wfi.create_requirement("ResourceRequirement", "ramMax", 4096)},
                inputs={"output1.txt", "output2.txt", "output3.txt"},
                outputs={"output.txt"}),
        ]
        return tasks


if __name__ == "__main__":
    unittest.main()
