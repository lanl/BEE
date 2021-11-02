#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

from beeflow.common.wf_data import Requirement, Hint
from beeflow.common.wf_interface import WorkflowInterface


class TestWorkflowInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the Workflow interface."""
        cls.wfi = WorkflowInterface()

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        if self.wfi.workflow_initialized() and self.wfi.workflow_loaded():
            self.wfi.finalize_workflow()

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The workflow node and associated requirement/hint nodes should have been created.
        """
        requirements = [self.wfi.create_requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [self.wfi.create_hint("ResourceRequirement", {"ramMin": 1024}),
                 self.wfi.create_hint("NetworkAccess", {"networkAccess": True})]
        workflow = self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"},
                                                requirements, hints)

        gdb_workflow, _ = self.wfi.get_workflow()

        self.assertEqual(gdb_workflow, workflow)
        self.assertEqual(gdb_workflow.id, workflow.id)
        self.assertIsNotNone(self.wfi._workflow_id)

    def test_execute_workflow(self):
        """Test workflow execution initialization (set initial tasks' states to 'READY')."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()
        self.wfi.execute_workflow()

        self.assertEqual(self.wfi.get_task_state(tasks[0]), "READY")

    def test_pause_workflow(self):
        """Test workflow execution pausing (set running tasks' states to 'PAUSED')."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()

        # Set Compute tasks to RUNNING
        for task in tasks[1:4]:
            self.wfi.set_task_state(task, "RUNNING")
        self.wfi.pause_workflow()

        # Compute tasks should now be PAUSED
        for task in tasks[1:4]:
            self.assertEqual("PAUSED", self.wfi.get_task_state(task))

        # No other tasks should be affected
        self.assertEqual("WAITING", self.wfi.get_task_state(tasks[0]))
        self.assertEqual("WAITING", self.wfi.get_task_state(tasks[4]))

    def test_resume_workflow(self):
        """Test workflow execution resuming (set paused tasks' states to 'RUNNING')."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()

        # Set Compute tasks to PAUSED
        for task in tasks[1:4]:
            self.wfi.set_task_state(task, "PAUSED")
        self.wfi.resume_workflow()

        # Compute tasks should now be PAUSED
        for task in tasks[1:4]:
            self.assertEqual("RUNNING", self.wfi.get_task_state(task))

        # No other tasks should be affected
        self.assertEqual("WAITING", self.wfi.get_task_state(tasks[0]))
        self.assertEqual("WAITING", self.wfi.get_task_state(tasks[4]))

    def test_reset_workflow(self):
        """Test workflow execution resetting (set all tasks to 'WAITING', delete metadata)."""
        workflow = self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}
        empty_metadata = {"cluster": None, "crt": None, "container_md5": None, "job_id": None}

        # Set tasks' metadata, set state to COMPLETED
        for task in tasks:
            self.wfi.set_task_metadata(task, metadata)
            self.wfi.set_task_state(task, "COMPLETED")
            self.assertEqual("COMPLETED", self.wfi.get_task_state(task))

        self.wfi.reset_workflow()

        # States should be reset, metadata should be deleted
        for task in tasks:
            self.assertDictEqual(empty_metadata, self.wfi.get_task_metadata(task, metadata.keys()))
            self.assertEqual("WAITING", self.wfi.get_task_state(task))

        # Workflow ID should be reset
        (gdb_workflow, gdb_tasks) = self.wfi.get_workflow()
        new_workflow_id = gdb_workflow.id

        self.assertNotEqual(new_workflow_id, workflow.id)
        for task in gdb_tasks:
            self.assertEqual(task.workflow_id, new_workflow_id)

    def test_finalize_workflow(self):
        """Test workflow deletion from the graph database."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        self.wfi.finalize_workflow()

        self.assertFalse(self.wfi.workflow_loaded())

    def test_add_task(self):
        """Test task creation."""
        task_name = "Test Task"
        command = ["ls", "-a", "-l", "-F"]
        requirements = [self.wfi.create_requirement("ResourceRequirement", {"ramMin": 1024}),
                        self.wfi.create_requirement("NetworkAccess", {"networkAccess": True})]
        hints = [self.wfi.create_hint("ResourceRequirement", {"ramMin": 1024}),
                 self.wfi.create_hint("NetworkAccess", {"networkAccess": True})]
        subworkflow = "Test Subworkflow"
        inputs = {"input.txt"}
        outputs = {"test_task_done"}

        workflow = self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"test_task_done"})
        task = self.wfi.add_task(
            name=task_name,
            command=command,
            requirements=requirements,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        # Task object assertions
        self.assertEqual(task_name, task.name)
        self.assertListEqual(command, task.command)
        self.assertCountEqual(requirements, task.requirements)
        self.assertCountEqual(hints, task.hints)
        self.assertEqual(subworkflow, task.subworkflow)
        self.assertSetEqual(inputs, task.inputs)
        self.assertSetEqual(outputs, task.outputs)
        self.assertEqual(task.workflow_id, self.wfi._workflow_id)
        self.assertIsInstance(task.id, str)

        # Graph database assertions
        gdb_task = self.wfi.get_task_by_id(task.id)
        self.assertEqual(task, gdb_task)
        self.assertEqual(task.id, gdb_task.id)

    def test_initialize_ready_tasks(self):
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()

        # Not using finalize_task() to test independent use of initialize_ready_tasks()
        self.wfi.set_task_state(tasks[0], "COMPLETED")
        self.wfi.initialize_ready_tasks()

        self.assertEqual("READY", self.wfi.get_task_state(tasks[1]))
        self.assertEqual("READY", self.wfi.get_task_state(tasks[2]))
        self.assertEqual("READY", self.wfi.get_task_state(tasks[3]))

    def test_finalize_task(self):
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()

        ready_tasks = self.wfi.finalize_task(tasks[0])

        self.assertSetEqual(set(tasks[1:4]), ready_tasks)

    def test_create_requirement(self):
        """Test workflow requirement creation."""
        req_class = "ResourceRequirement"
        req_params = {"ramMin": 1024}

        req = self.wfi.create_requirement(req_class, req_params)

        self.assertIsInstance(req, Requirement)
        self.assertEqual(req_class, req.class_)
        self.assertEqual(req_params, req.params)

    def test_create_hint(self):
        """Test workflow hint creation."""
        hint_class = "NetworkAccess"
        hint_params = {"networkAccess": True}

        hint = self.wfi.create_hint(hint_class, hint_params)

        self.assertIsInstance(hint, Hint)
        self.assertEqual(hint_class, hint.class_)
        self.assertEqual(hint_params, hint.params)

    def test_get_task_by_id(self):
        """Test obtaining a task from the graph database by its ID."""
        task_name = "Test Task"
        command = ["ls", "-a", "-l", "-F"]
        requirements = [self.wfi.create_requirement("ResourceRequirement", {"ramMin": 1024}),
                        self.wfi.create_requirement("NetworkAccess", {"networkAccess": True})]
        hints = [self.wfi.create_hint("ResourceRequirement", {"ramMin": 1024}),
                 self.wfi.create_hint("NetworkAccess", {"networkAccess": True})]
        subworkflow = "Test Subworkflow"
        inputs = {"input.txt"}
        outputs = {"test_task_done"}

        workflow = self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"test_task_done"})
        task = self.wfi.add_task(
            name=task_name,
            command=command,
            requirements=requirements,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        self.assertEqual(task, self.wfi.get_task_by_id(task.id))

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        requirements = [self.wfi.create_requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [self.wfi.create_hint("NetworkAccess", {"networkAccess": True})]
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"}, requirements,
                                     hints)
        tasks = self._create_test_tasks()

        (workflow, wf_tasks) = self.wfi.get_workflow()

        self.assertSetEqual(set(tasks), wf_tasks)
        self.assertCountEqual(requirements, workflow.requirements)
        self.assertCountEqual(hints, workflow.hints)

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        requirements = [self.wfi.create_requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [self.wfi.create_hint("NetworkAccess", {"networkAccess": True})]
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"}, requirements,
                                     hints)
        tasks = self._create_test_tasks()

        # Subworkflow assertion
        (subwf_tasks, subwf_requirements, subwf_hints) = self.wfi.get_subworkflow("Compute")
        self.assertSetEqual(set(tasks[1:4]), subwf_tasks)
        self.assertCountEqual(requirements, subwf_requirements)
        self.assertCountEqual(hints, subwf_hints)

    def test_get_ready_tasks(self):
        """Test obtaining of ready workflow tasks."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()

        # Should be no ready tasks
        self.assertSetEqual(set(), self.wfi.get_ready_tasks())

        # Set Compute tasks to READY
        for task in tasks[1:4]:
            self.wfi.set_task_state(task, "READY")

        self.assertSetEqual(set(tasks[1:4]), self.wfi.get_ready_tasks())

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        tasks = self._create_test_tasks()
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wfi.get_dependent_tasks(tasks[0])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertSetEqual(set(tasks[1:4]), set(dependent_tasks))

    def test_get_task_state(self):
        """Test obtaining of task state."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")

        # Should be WAITING because workflow not yet executed
        self.assertEqual("WAITING", self.wfi.get_task_state(task))

    def test_set_task_state(self):
        """Test the setting of task state."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")

        self.wfi.set_task_state(task, "RUNNING")

        # Should now be RUNNING
        self.assertEqual("RUNNING", self.wfi.get_task_state(task))

    def test_get_task_metadata(self):
        """Test the obtaining of task metadata."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        self.wfi.set_task_metadata(task, metadata)
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task, metadata.keys()))

    def test_set_task_metadata(self):
        """Test the setting of task metadata."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}
        empty_metadata = {"cluster": None, "crt": None, "container_md5": None, "job_id": None}

        # Metadata should be empty
        self.assertDictEqual(empty_metadata, self.wfi.get_task_metadata(task, metadata.keys()))

        self.wfi.set_task_metadata(task, metadata)

        # Metadata should now be populated
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task, metadata.keys()))

    def test_workflow_completed(self):
        """Test determining if a workflow has completed."""
        workflow = self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        task = self.wfi.add_task("Test Task")

        # Workflow not completed
        self.assertFalse(self.wfi.workflow_completed())

        # Not using finalize_task() to avoid unnecessary queries
        self.wfi.set_task_state(task, 'COMPLETED')

        # Workflow now completed
        self.assertTrue(self.wfi.workflow_completed())

    def test_workflow_initialized(self):
        """Test determining if a workflow is initialized."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})

        # Workflow now initialized
        self.assertTrue(self.wfi.workflow_initialized())

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})
        self.wfi.finalize_workflow()

        # Workflow not loaded
        self.assertFalse(self.wfi.workflow_loaded())

        self.wfi.initialize_workflow("Test Workflow", {"input.txt"}, {"output.txt"})

        # Workflow now loaded
        self.assertTrue(self.wfi.workflow_loaded())

    def _create_test_tasks(self):
        """Create test tasks to reduce redundancy."""
        # Remember that add_task uploads the task to the database as well as returns a Task
        tasks = [
            self.wfi.add_task(
                "Data Prep", command=["ls", "-a", "-l", "-F"],
                requirements=[self.wfi.create_requirement("NetworkAccess",
                                                          {"networkAccess": True})],
                hints=[self.wfi.create_hint("ResourceRequirement", {"ramMax": 2048})],
                inputs={"input.txt"}, outputs={"prep_input.txt"}),
            self.wfi.add_task(
                "Compute 0", command=["rm", "-r", "-f"],
                requirements=[self.wfi.create_requirement("NetworkAccess",
                                                          {"networkAccess": True})],
                hints=[self.wfi.create_hint("ResourceRequirement", {"ramMax": 2048})],
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output1.txt"}),
            self.wfi.add_task(
                "Compute 1", command=["find"],
                requirements=[self.wfi.create_requirement("NetworkAccess",
                                                          {"networkAccess": True})],
                hints=[self.wfi.create_hint("ResourceRequirement", {"ramMax": 2048})],
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output2.txt"}),
            self.wfi.add_task(
                "Compute 2", command=["yes"],
                requirements=[self.wfi.create_requirement("NetworkAccess",
                                                          {"networkAccess": True})],
                hints=[self.wfi.create_hint("ResourceRequirement", {"ramMax": 2048})],
                subworkflow="Compute", inputs={"prep_input.txt"},
                outputs={"output3.txt"}),
            self.wfi.add_task(
                "Visualization", command=["ln", "-s"],
                requirements=[self.wfi.create_requirement("NetworkAccess",
                                                          {"networkAccess": True})],
                hints=[self.wfi.create_hint("ResourceRequirement", {"ramMax": 2048})],
                inputs={"output1.txt", "output2.txt", "output3.txt"},
                outputs={"output.txt"}),
        ]
        return tasks


if __name__ == "__main__":
    unittest.main()
