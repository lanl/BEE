#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

from beeflow.common.wf_data import (Requirement, Hint, InputParameter, OutputParameter,
                                    StepInput, StepOutput)
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
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True})]
        workflow = self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "viz/output")},
            requirements, hints)

        gdb_workflow, _ = self.wfi.get_workflow()

        self.assertEqual(gdb_workflow, workflow)
        self.assertEqual(gdb_workflow.id, workflow.id)
        self.assertIsNotNone(self.wfi._workflow_id)

    def test_execute_workflow(self):
        """Test workflow execution initialization (set initial tasks' states to 'READY')."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        tasks = self._create_test_tasks()
        self.wfi.execute_workflow()

        self.assertEqual(self.wfi.get_task_state(tasks[0]), "READY")

    def test_pause_workflow(self):
        """Test workflow execution pausing (set running tasks' states to 'PAUSED')."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
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
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
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
        workflow = self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "viz/output")})
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
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        self.wfi.finalize_workflow()

        self.assertFalse(self.wfi.workflow_loaded())

    def test_add_task(self):
        """Test task creation."""
        task_name = "test_task"
        base_command = ["ls", "-a", "-F"]
        inputs = {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", "-l",
                            None)}
        outputs = {StepOutput("test_input/test_task_done", "stdout", "output.txt", "output.txt")}
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024}),
                        Requirement("NetworkAccess", {"networkAccess": True})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True})]
        stdout = "output.txt"

        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "test_input/test_task_done")})
        task = self.wfi.add_task(
            name=task_name,
            base_command=base_command,
            inputs=inputs,
            outputs=outputs,
            requirements=requirements,
            hints=hints,
            stdout=stdout)

        # Task object assertions
        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertSetEqual(inputs, task.inputs)
        self.assertSetEqual(outputs, task.outputs)
        self.assertCountEqual(requirements, task.requirements)
        self.assertCountEqual(hints, task.hints)
        self.assertEqual(stdout, task.stdout)
        self.assertEqual(task.workflow_id, self.wfi._workflow_id)
        self.assertIsInstance(task.id, str)

        # Graph database assertions
        gdb_task = self.wfi.get_task_by_id(task.id)
        self.assertEqual(task, gdb_task)
        self.assertEqual(task.id, gdb_task.id)

    def test_initialize_ready_tasks(self):
        """Test initialization of tasks that are ready to run."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        tasks = self._create_test_tasks()

        # Not using finalize_task() to test independent use of initialize_ready_tasks()
        self.wfi.set_task_state(tasks[0], "COMPLETED")
        self.wfi.initialize_ready_tasks()

        self.assertEqual("READY", self.wfi.get_task_state(tasks[1]))
        self.assertEqual("READY", self.wfi.get_task_state(tasks[2]))
        self.assertEqual("READY", self.wfi.get_task_state(tasks[3]))

    def test_finalize_task(self):
        """Test finalization of completed tasks."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        tasks = self._create_test_tasks()

        ready_tasks = self.wfi.finalize_task(tasks[0])

        self.assertSetEqual(set(tasks[1:4]), ready_tasks)

    def test_get_task_by_id(self):
        """Test obtaining a task from the graph database by its ID."""
        task_name = "test_task"
        base_command = "ls"
        inputs = {StepInput("input", "File", "input.txt", "default.txt", "test_input", None, None)}
        outputs = {StepOutput("test_task/test_task_done", "stdout", "output.txt", "output.txt")}
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024}),
                        Requirement("NetworkAccess", {"networkAccess": True})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True})]
        stdout = "output.txt"

        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "test_task/test_task_done")})
        task = self.wfi.add_task(
            name=task_name,
            base_command=base_command,
            inputs=inputs,
            outputs=outputs,
            requirements=requirements,
            hints=hints,
            stdout=stdout)

        self.assertEqual(task, self.wfi.get_task_by_id(task.id))

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [Hint("NetworkAccess", {"networkAccess": True})]
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")}, requirements, hints)
        tasks = self._create_test_tasks()

        (workflow, wf_tasks) = self.wfi.get_workflow()

        self.assertSetEqual(set(tasks), wf_tasks)
        self.assertCountEqual(requirements, workflow.requirements)
        self.assertCountEqual(hints, workflow.hints)

    def test_get_ready_tasks(self):
        """Test obtaining of ready workflow tasks."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        tasks = self._create_test_tasks()

        # Should be no ready tasks
        self.assertSetEqual(set(), self.wfi.get_ready_tasks())

        # Set Compute tasks to READY
        for task in tasks[1:4]:
            self.wfi.set_task_state(task, "READY")

        self.assertSetEqual(set(tasks[1:4]), self.wfi.get_ready_tasks())

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        tasks = self._create_test_tasks()
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wfi.get_dependent_tasks(tasks[0])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertSetEqual(set(tasks[1:4]), set(dependent_tasks))

    def test_get_task_state(self):
        """Test obtaining of task state."""
        self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "test_task/output")})
        task = self.wfi.add_task(
            "test_task",
            "ls",
            {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None)},
            {StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")})

        # Should be WAITING because workflow not yet executed
        self.assertEqual("WAITING", self.wfi.get_task_state(task))

    def test_set_task_state(self):
        """Test the setting of task state."""
        self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "test_task/output")})
        task = self.wfi.add_task(
            "test_task",
            "ls",
            {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None)},
            {StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")})

        self.wfi.set_task_state(task, "RUNNING")

        # Should now be RUNNING
        self.assertEqual("RUNNING", self.wfi.get_task_state(task))

    def test_get_task_metadata(self):
        """Test the obtaining of task metadata."""
        self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "test_task/output")})
        task = self.wfi.add_task(
            "test_task",
            "ls",
            {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None)},
            {StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")})
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        self.wfi.set_task_metadata(task, metadata)
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task, metadata.keys()))

    def test_set_task_metadata(self):
        """Test the setting of task metadata."""
        self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "test_task/output")})
        task = self.wfi.add_task(
            "test_task",
            "ls",
            {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None)},
            {StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")})
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
        self.wfi.initialize_workflow(
            "test_workflow",
            {InputParameter("test_input", "File", "input.txt")},
            {OutputParameter("test_output", "File", "output.txt", "test_task/output")})
        task = self.wfi.add_task(
            "test_task",
            "ls",
            {StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None)},
            {StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")})

        # Workflow not completed
        self.assertFalse(self.wfi.workflow_completed())

        # Not using finalize_task() to avoid unnecessary queries
        self.wfi.set_task_state(task, 'COMPLETED')

        # Workflow now completed
        self.assertTrue(self.wfi.workflow_completed())

    def test_workflow_initialized(self):
        """Test determining if a workflow is initialized."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})

        # Workflow now initialized
        self.assertTrue(self.wfi.workflow_initialized())

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})
        self.wfi.finalize_workflow()

        # Workflow not loaded
        self.assertFalse(self.wfi.workflow_loaded())

        self.wfi.initialize_workflow("test_workflow",
                                     {InputParameter("test_input", "File", "input.txt")},
                                     {OutputParameter("test_output", "File", "output.txt",
                                                      "viz/output")})

        # Workflow now loaded
        self.assertTrue(self.wfi.workflow_loaded())

    def test_workflow_id(self):
        """Test retrieving the workflow ID from the workflow interface."""
        self.assertEqual(self.wfi.workflow_id, self.wfi._workflow_id)

        # Set workflow_id to None so it's retrieved from database
        self.wfi._workflow_id = None

        self.assertEqual(self.wfi.workflow_id, self.wfi._workflow_id)

    def _create_test_tasks(self):
        """Create test tasks to reduce redundancy."""
        # Remember that add_task uploads the task to the database as well as returns a Task
        tasks = [
            self.wfi.add_task(
                "data_prep", base_command=["ls", "-a", "-F"],
                inputs={StepInput("test_input", "File", "input.txt", None, "test_input", "-l",
                                  None)},
                outputs={StepOutput("prep/prep_output.txt", "stdout", "prep_output.txt",
                                    "prep_output.txt")},
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="prep_output.txt"),
            self.wfi.add_task(
                "compute0", base_command="touch",
                inputs={StepInput("input_data", "File", "prep_input.txt", None,
                                  "prep/prep_output.txt", None, None)},
                outputs={StepOutput("compute0/output", "stdout", "output.txt", "output.txt")},
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output.txt"),
            self.wfi.add_task(
                "compute1", base_command="find",
                inputs={StepInput("input_data", "File", "prep_input.txt", None,
                                  "prep/prep_output.txt", None, None)},
                outputs={StepOutput("compute1/output", "stdout", "output.txt", "output.txt")},
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output.txt"),
            self.wfi.add_task(
                "compute2", base_command="grep",
                inputs={StepInput("input_data", "File", "prep_input.txt", None,
                                  "prep/prep_output.txt", None, None)},
                outputs={StepOutput("compute2/output", "stdout", "output.txt", "output.txt")},
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output.txt"),
            self.wfi.add_task(
                "visualization", base_command="python",
                inputs={StepInput("input0", "File", "output.txt", None, "compute0/output", "-i",
                                  1),
                        StepInput("input1", "File", "output.txt", None, "compute1/output", "-i",
                                  2),
                        StepInput("input2", "File", "output.txt", None, "compute2/output", "-i",
                                  3)},
                outputs={StepOutput("viz/output", "stdout", "viz_output.txt", "viz_output.txt")},
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="viz_output.txt")
        ]
        return tasks


if __name__ == "__main__":
    unittest.main()
