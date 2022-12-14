#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

from beeflow.common.config_driver import BeeConfig as bc

bc.init()

from beeflow.common.wf_data import (Requirement, Hint, InputParameter, OutputParameter,
                                    StepInput, StepOutput, generate_workflow_id)
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.tests.mocks import MockGDBInterface


class TestWorkflowInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Start the GDB and initialize the Workflow interface."""
        mock_gdb_iface = MockGDBInterface()
        cls.wfi = WorkflowInterface(mock_gdb_iface)

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
        workflow_id = generate_workflow_id()
        workflow = self.wfi.initialize_workflow(
            workflow_id, "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")],
            requirements, hints)

        gdb_workflow, _ = self.wfi.get_workflow()

        self.assertEqual(workflow, gdb_workflow)
        self.assertEqual(workflow_id, workflow.id)
        self.assertEqual(workflow.id, gdb_workflow.id)
        self.assertIsNotNone(self.wfi._workflow_id)
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

    def test_execute_workflow(self):
        """Test workflow execution initialization (set initial tasks' states to 'READY')."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        tasks = self._create_test_tasks()
        self.wfi.execute_workflow()

        self.assertEqual("READY", self.wfi.get_task_state(tasks[0]))
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_pause_workflow(self):
        """Test workflow execution pausing (set running tasks' states to 'PAUSED')."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        self._create_test_tasks()

        self.wfi.execute_workflow()

        self.wfi.pause_workflow()

        # Workflow state should now be 'PAUSED'
        self.assertEqual("PAUSED", self.wfi.get_workflow_state())

    def test_resume_workflow(self):
        """Test workflow execution resuming (set paused tasks' states to 'RUNNING')."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        self._create_test_tasks()

        self.wfi.execute_workflow()
        self.wfi.pause_workflow()
        self.wfi.resume_workflow()

        # Workflow state should now be 'RESUME'
        self.assertEqual("RESUME", self.wfi.get_workflow_state())

    def test_reset_workflow(self):
        """Test workflow execution resetting (set all tasks to 'WAITING', delete metadata)."""
        workflow = self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        tasks = self._create_test_tasks()
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        # Set tasks' metadata, set state to COMPLETED
        for task in tasks:
            self.wfi.set_task_metadata(task, metadata)
            self.wfi.set_task_state(task, "COMPLETED")
            self.assertEqual("COMPLETED", self.wfi.get_task_state(task))

        workflow_id = 42
        self.wfi.reset_workflow(workflow_id)

        # States should be reset, metadata should be deleted
        for task in tasks:
            self.assertDictEqual({}, self.wfi.get_task_metadata(task))
            self.assertEqual("WAITING", self.wfi.get_task_state(task))

        # Workflow ID should be reset
        (gdb_workflow, gdb_tasks) = self.wfi.get_workflow()
        new_workflow_id = gdb_workflow.id

        self.assertNotEqual(new_workflow_id, workflow.id)
        for task in gdb_tasks:
            self.assertEqual(task.workflow_id, new_workflow_id)

    def test_finalize_workflow(self):
        """Test workflow deletion from the graph database."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        self.wfi.finalize_workflow()

        self.assertFalse(self.wfi.workflow_loaded())

    def test_add_task(self):
        """Test task creation."""
        task_name = "test_task"
        base_command = ["ls", "-a", "-F"]
        inputs = [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", "-l",
                            None, None)]
        outputs = [StepOutput("test_input/test_task_done", "stdout", "output.txt", "output.txt")]
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024}),
                        Requirement("NetworkAccess", {"networkAccess": True})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True})]
        stdout = "output.txt"
        stderr = "output-err.txt"

        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_input/test_task_done")])
        task = self.wfi.add_task(
            name=task_name,
            base_command=base_command,
            inputs=inputs,
            outputs=outputs,
            requirements=requirements,
            hints=hints,
            stdout=stdout,
            stderr=stderr)

        # Task object assertions
        self.assertEqual(task_name, task.name)
        self.assertEqual(base_command, task.base_command)
        self.assertCountEqual(inputs, task.inputs)
        self.assertCountEqual(outputs, task.outputs)
        self.assertCountEqual(requirements, task.requirements)
        self.assertCountEqual(hints, task.hints)
        self.assertEqual(stdout, task.stdout)
        self.assertEqual(stderr, task.stderr)
        self.assertEqual(task.workflow_id, self.wfi._workflow_id)
        self.assertIsInstance(task.id, str)

        # Graph database assertions
        gdb_task = self.wfi.get_task_by_id(task.id)
        self.assertEqual(task, gdb_task)
        self.assertEqual(task.id, gdb_task.id)

    def test_restart_task(self):
        """Test restart of failed task."""
        task_name = "test_task"
        base_command = ["ls", "-a", "-F"]
        inputs = [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", "-l",
                            None, None)]
        outputs = [StepOutput("test_input/test_task_done", "stdout", "output.txt", "output.txt")]
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024}),
                        Requirement("NetworkAccess", {"networkAccess": True})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True}),
                 Hint("beeflow:CheckpointRequirement", {"file_path": "checkpoint_output",
                                                        "container_path": "checkpoint_output",
                                                        "file_regex": "backup[0-9]*.crx",
                                                        "restart_parameters": "-R",
                                                        "num_tries": 2})]
        stdout = "output.txt"
        stderr = "output-err.txt"
        test_checkpoint_file = "/backup0.crx"

        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_input/test_task_done")])
        task = self.wfi.add_task(
            name=task_name,
            base_command=base_command,
            inputs=inputs,
            outputs=outputs,
            requirements=requirements,
            hints=hints,
            stdout=stdout,
            stderr=stderr)

        # Restart the task, should create a new Task
        new_task = self.wfi.restart_task(task, test_checkpoint_file)

        # Assert inequality of Task objects
        self.assertNotEqual(task.id, new_task.id)
        self.assertEqual("test_task(1)", new_task.name)

        # Assert equality of graph database objects
        self.assertEqual(new_task, self.wfi.get_task_by_id(new_task.id))
        self.assertEqual("RESTARTED", self.wfi.get_task_state(task))
        self.assertEqual("READY", self.wfi.get_task_state(new_task))
        self.assertEqual(self.wfi.get_task_metadata(task),
                         self.wfi.get_task_metadata(new_task))

        # Check that task command includes checkpoint file
        print(new_task.command)
        self.assertListEqual(['ls', '-a', '-F', '-l', 'input.txt', '-R',
                              '/backup0.crx'], new_task.command)

        # Restart once again
        newer_task = self.wfi.restart_task(new_task, test_checkpoint_file)

        # Assert inequality of Task objects
        self.assertNotEqual(new_task.id, newer_task.id)
        self.assertEqual("test_task(2)", newer_task.name)

        # Assert equality of graph database objects
        self.assertEqual(newer_task, self.wfi.get_task_by_id(newer_task.id))
        self.assertEqual("RESTARTED", self.wfi.get_task_state(new_task))
        self.assertEqual("READY", self.wfi.get_task_state(newer_task))
        self.assertEqual(self.wfi.get_task_metadata(new_task),
                         self.wfi.get_task_metadata(newer_task))

        # Restart on more time (should return None)
        self.assertIsNone(self.wfi.restart_task(newer_task, test_checkpoint_file))

        # Check that task command includes checkpoint file
        self.assertListEqual(['ls', '-a', '-F', '-l', 'input.txt', '-R',
                              '/backup0.crx'], newer_task.command)

    def test_finalize_task(self):
        """Test finalization of completed tasks."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        tasks = self._create_test_tasks()
        self.wfi.execute_workflow()
        self.wfi.set_task_output(tasks[0], "prep/prep_output", "prep_output.txt")
        ready_tasks = self.wfi.finalize_task(tasks[0])

        # Manually set expected task input values for comparison
        tasks[1].inputs = [StepInput("input_data", "File", "prep_output.txt", None,
                                     "prep/prep_output", None, None, None)]
        tasks[2].inputs = [StepInput("input_data", "File", "prep_output.txt", None,
                                     "prep/prep_output", None, None, None)]
        tasks[3].inputs = [StepInput("input_data", "File", "prep_output.txt", None,
                                     "prep/prep_output", None, None, None)]

        self.assertCountEqual(tasks[1:4], ready_tasks)

    def test_get_task_by_id(self):
        """Test obtaining a task from the graph database by its ID."""
        task_name = "test_task"
        base_command = "ls"
        inputs = [StepInput("input", "File", "input.txt", "default.txt", "test_input", None, None,
                            None)]
        outputs = [StepOutput("test_task/test_task_done", "stdout", "output.txt", "output.txt")]
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024}),
                        Requirement("NetworkAccess", {"networkAccess": True})]
        hints = [Hint("ResourceRequirement", {"ramMin": 1024}),
                 Hint("NetworkAccess", {"networkAccess": True})]
        stdout = "output.txt"
        stderr = "output-err.txt"

        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/test_task_done")])
        task = self.wfi.add_task(
            name=task_name,
            base_command=base_command,
            inputs=inputs,
            outputs=outputs,
            requirements=requirements,
            hints=hints,
            stdout=stdout,
            stderr=stderr)

        self.assertEqual(task, self.wfi.get_task_by_id(task.id))

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        requirements = [Requirement("ResourceRequirement", {"ramMin": 1024})]
        hints = [Hint("NetworkAccess", {"networkAccess": True})]
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")],
            requirements, hints)
        tasks = self._create_test_tasks()

        (workflow, wf_tasks) = self.wfi.get_workflow()

        self.assertCountEqual(tasks, wf_tasks)
        self.assertCountEqual(requirements, workflow.requirements)
        self.assertCountEqual(hints, workflow.hints)

    def test_get_workflow_outputs(self):
        """Test obtaining the outputs of a workflow."""
        workflow = self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/test_task_done")])

        self.assertListEqual(workflow.outputs, self.wfi.get_workflow_outputs())

    def test_get_workflow_state(self):
        """Test obtaining the state of a workflow."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/test_task_done")])

        # Initialized workflow state should be 'SUBMITTED'
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

        self.wfi.execute_workflow()

        # Executed workflow state should be 'RUNNING'
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_set_workflow_state(self):
        """Test setting the state of a workflow."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/test_task_done")])

        # Initialized workflow state should be 'SUBMITTED'
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

        self.wfi.set_workflow_state("RUNNING")

        # Workflow state should now be 'RUNNING'
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_get_ready_tasks(self):
        """Test obtaining of ready workflow tasks."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        tasks = self._create_test_tasks()

        # Should be no ready tasks
        self.assertListEqual([], self.wfi.get_ready_tasks())

        # Set Compute tasks to READY
        for task in tasks[1:4]:
            self.wfi.set_task_state(task, "READY")

        self.assertCountEqual(tasks[1:4], self.wfi.get_ready_tasks())

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        tasks = self._create_test_tasks()
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wfi.get_dependent_tasks(tasks[0])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertCountEqual(tasks[1:4], dependent_tasks)

    def test_get_task_state(self):
        """Test obtaining of task state."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])

        # Should be WAITING because workflow not yet executed
        self.assertEqual("WAITING", self.wfi.get_task_state(task))

    def test_set_task_state(self):
        """Test the setting of task state."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])

        self.wfi.set_task_state(task, "RUNNING")

        # Should now be RUNNING
        self.assertEqual("RUNNING", self.wfi.get_task_state(task))

    def test_get_task_metadata(self):
        """Test the obtaining of task metadata."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        self.wfi.set_task_metadata(task, metadata)
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task))

    def test_set_task_metadata(self):
        """Test the setting of task metadata."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        # Metadata should be empty
        self.assertDictEqual({}, self.wfi.get_task_metadata(task))

        self.wfi.set_task_metadata(task, metadata)

        # Metadata should now be populated
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task))

    def test_get_task_input(self):
        """Test the obtaining of a task input."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])

        self.assertEqual(task.inputs[0], self.wfi.get_task_input(task, "test_input"))

    def test_set_task_input(self):
        """Test the setting of a task input."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", None, "default.txt", "test_input", None, None, None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])

        test_input = StepInput("test_input", "File", "input.txt", "default.txt", "test_input",
                               None, None, None)
        self.wfi.set_task_input(task, "test_input", "input.txt")
        self.assertEqual(test_input, self.wfi.get_task_input(task, "test_input"))

    def test_get_task_output(self):
        """Test the obtaining of a task output."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       None)],
            [StepOutput("test_task/output", "File", "output.txt", "output.txt")])

        self.assertEqual(task.outputs[0], self.wfi.get_task_output(task, "test_task/output"))

    def test_set_task_output(self):
        """Test the setting of a task output."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None, None)],
            [StepOutput("test_task/output", "File", None, "output.txt")])

        test_output = StepOutput("test_task/output", "File", "output.txt", "output.txt")
        self.wfi.set_task_output(task, "test_task/output", "output.txt")
        self.assertEqual(test_output, self.wfi.get_task_output(task, "test_task/output"))

    def test_evaluate_expression(self):
        """Test the evaluation of an input/output expression."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None, None,
                       '$("test_" + inputs.test_input)')],
            [StepOutput("test_task/output", "File", None, "$(inputs.test_input).bak")])

        test_input = StepInput("test_input", "string", "test_input.txt", "default.txt",
                               "test_input", None, None, '$("test_" + inputs.test_input)')
        self.wfi.evaluate_expression(task, "test_input")
        self.assertEqual(test_input, self.wfi.get_task_input(task, "test_input"))

        test_output = StepOutput("test_task/output", "File", None, "test_input.txt.bak")
        self.wfi.evaluate_expression(task, "test_task/output", output=True)
        self.assertEqual(test_output, self.wfi.get_task_output(task, "test_task/output"))

    def test_workflow_completed(self):
        """Test determining if a workflow has completed."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "test_task/output")])
        task = self.wfi.add_task(
            "test_task",
            "ls",
            [StepInput("test_input", "File", "input.txt", "default.txt", "test_input", None,
                       None, None)],
            [StepOutput("test_task/output", "File", "output.txt",
                        "output.txt")])

        # Workflow not completed
        self.assertFalse(self.wfi.workflow_completed())

        # Not using finalize_task() to avoid unnecessary queries
        self.wfi.set_task_state(task, 'COMPLETED')

        # Workflow now completed
        self.assertTrue(self.wfi.workflow_completed())

    def test_workflow_initialized(self):
        """Test determining if a workflow is initialized."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])

        # Workflow now initialized
        self.assertTrue(self.wfi.workflow_initialized())

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])
        self.wfi.finalize_workflow()

        # Workflow not loaded
        self.assertFalse(self.wfi.workflow_loaded())

        self.wfi.initialize_workflow(
            generate_workflow_id(), "test_workflow",
            [InputParameter("test_input", "File", "input.txt")],
            [OutputParameter("test_output", "File", "output.txt", "viz/output")])

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
                inputs=[StepInput("test_input", "File", None, None, "test_input", "-l", None,
                                  None)],
                outputs=[StepOutput("prep/prep_output", "stdout", None, "prep_output.txt")],
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="prep_output.txt"),
            self.wfi.add_task(
                "compute0", base_command="touch",
                inputs=[StepInput("input_data", "File", None, None, "prep/prep_output", None,
                                  None, None)],
                outputs=[StepOutput("compute0/output", "stdout", None, "output0.txt")],
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output0.txt"),
            self.wfi.add_task(
                "compute1", base_command="find",
                inputs=[StepInput("input_data", "File", None, None, "prep/prep_output", None,
                                  None, None)],
                outputs=[StepOutput("compute1/output", "stdout", None, "output1.txt")],
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output1.txt"),
            self.wfi.add_task(
                "compute2", base_command="grep",
                inputs=[StepInput("input_data", "File", None, None, "prep/prep_output", None,
                                  None, None)],
                outputs=[StepOutput("compute2/output", "stdout", None, "output2.txt")],
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="output2.txt"),
            self.wfi.add_task(
                "visualization", base_command="python",
                inputs=[StepInput("input0", "File", None, None, "compute0/output", "-i", 1, None),
                        StepInput("input1", "File", None, None, "compute1/output", "-i", 2, None),
                        StepInput("input2", "File", None, None, "compute2/output", "-i", 3, None)],
                outputs=[StepOutput("viz/output", "stdout", "viz_output.txt", "viz_output.txt")],
                requirements=[Requirement("NetworkAccess", {"networkAccess": True})],
                hints=[Hint("ResourceRequirement", {"ramMax": 2048})], stdout="viz_output.txt")
        ]
        return tasks


if __name__ == "__main__":
    unittest.main()
