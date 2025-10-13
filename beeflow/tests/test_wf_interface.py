#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable W0212: Access required for unit tests
# pylint:disable=W0212

import unittest

from beeflow.common.object_models import (Workflow, Task, Requirement, Hint, InputParameter,
                                    OutputParameter, StepInput, StepOutput, generate_workflow_id)
from beeflow.common.wf_interface import WorkflowInterface
from beeflow.tests.mocks import MockGDBDriver


class TestWorkflowInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Start the GDB and initialize the Workflow interface."""
        mock_gdb_driver = MockGDBDriver()
        cls.wfi = WorkflowInterface(None, mock_gdb_driver)

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        self.wfi._gdb_driver.workflow = None
        self.wfi._gdb_driver.workflow_state = None
        self.wfi._gdb_driver.tasks.clear()
        self.wfi._gdb_driver.task_states.clear()
        self.wfi._gdb_driver.task_metadata.clear()
        self.wfi._gdb_driver.inputs.clear()
        self.wfi._gdb_driver.outputs.clear()

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The workflow node and associated requirement/hint nodes should have been created.
        """
        requirements = [Requirement(class_="ResourceRequirement", params={"ramMin": 1024})]
        hints = [Hint(class_="ResourceRequirement", params={"ramMin": 1024}),
                 Hint(class_="NetworkAccess", params={"networkAccess": True})]
        workflow_id = generate_workflow_id()
        workflow = Workflow(
            name="test_workflow", hints=hints, requirements=requirements,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id)

        self.wfi.initialize_workflow(workflow)

        gdb_workflow, _ = self.wfi.get_workflow()

        self.assertEqual(workflow, gdb_workflow)
        self.assertEqual(workflow_id, workflow.id)
        self.assertEqual(workflow.id, gdb_workflow.id)
        self.assertIsNotNone(self.wfi._workflow_id)
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

    def test_execute_workflow(self):
        """Test workflow execution initialization (set initial tasks' states to 'READY')."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        tasks = self._create_test_tasks(workflow_id)
        self.wfi.execute_workflow()

        self.assertEqual("READY", self.wfi.get_task_state(tasks[0].id))
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_pause_workflow(self):
        """Test workflow execution pausing (set running tasks' states to 'PAUSED')."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        self._create_test_tasks(workflow_id)

        self.wfi.execute_workflow()

        self.wfi.pause_workflow()

        # Workflow state should now be 'PAUSED'
        self.assertEqual("PAUSED", self.wfi.get_workflow_state())

    def test_resume_workflow(self):
        """Test workflow execution resuming (set paused tasks' states to 'RUNNING')."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        self._create_test_tasks(workflow_id)

        self.wfi.execute_workflow()
        self.wfi.pause_workflow()
        self.wfi.resume_workflow()

        # Workflow state should now be 'RESUME'
        self.assertEqual("RESUME", self.wfi.get_workflow_state())


    def test_add_task(self):
        """Test task creation."""
        task_name = "test_task"
        base_command = ["ls", "-a", "-F"]
        inputs = [StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix="-l",
                           position=None, value_from=None)]
        outputs = [StepOutput(id="test_input/test_task_done", type="stdout", value="output.txt", glob="output.txt")]
        requirements = [Requirement(class_="ResourceRequirement", params={"ramMin": 1024}),
                        Requirement(class_="NetworkAccess", params={"networkAccess": True})]
        hints = [Hint(class_="ResourceRequirement", params={"ramMin": 1024}),
                 Hint(class_="NetworkAccess", params={"networkAccess": True})]
        stdout = "output.txt"
        stderr = "output-err.txt"

        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_input/test_task_done")],
            id=workflow_id))

        task = Task(
            name=task_name,
            base_command=base_command,
            hints=hints,
            requirements=requirements,
            inputs=inputs,
            outputs=outputs,
            stdout=stdout,
            stderr=stderr,
            workflow_id=workflow_id)


        self.wfi.add_task(task)

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
        inputs = [StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix="-l",
                            position=None, value_from=None)]
        outputs = [StepOutput(id="test_input/test_task_done", type="stdout", value="output.txt", glob="output.txt")]
        requirements = [Requirement(class_="ResourceRequirement", params={"ramMin": 1024}),
                        Requirement(class_="NetworkAccess", params={"networkAccess": True})]
        hints = [Hint(class_="ResourceRequirement", params={"ramMin": 1024}),
                 Hint(class_="NetworkAccess", params={"networkAccess": True}),
                 Hint(class_="beeflow:CheckpointRequirement", params={"file_path": "checkpoint_output",
                                                                    "container_path": "checkpoint_output",
                                                                    "file_regex": "backup[0-9]*.crx",
                                                                    "restart_parameters": "-R",
                                                                    "num_tries": 2})]
        stdout = "output.txt"
        stderr = "output-err.txt"
        test_checkpoint_file = "/backup0.crx"

        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_input/test_task_done")],
            id=workflow_id))

        task = Task(
            name=task_name,
            base_command=base_command,
            hints=hints,
            requirements=requirements,
            inputs=inputs,
            outputs=outputs,
            stdout=stdout,
            stderr=stderr,
            workflow_id=workflow_id)


        self.wfi.add_task(task)

        # Restart the task, should create a new Task
        new_task = self.wfi.restart_task(task, test_checkpoint_file)

        # Assert inequality of Task objects
        self.assertNotEqual(task.id, new_task.id)
        self.assertEqual("test_task-1", new_task.name)

        # Assert equality of graph database objects
        self.assertEqual(new_task, self.wfi.get_task_by_id(new_task.id))
        self.assertEqual("RESTARTED", self.wfi.get_task_state(task.id))
        self.assertEqual("READY", self.wfi.get_task_state(new_task.id))
        self.assertEqual(self.wfi.get_task_metadata(task.id),
                         self.wfi.get_task_metadata(new_task.id))

        # Check that task command includes checkpoint file
        print(new_task.command)
        self.assertListEqual(['ls', '-a', '-F', '-l', 'input.txt', '-R',
                              '/backup0.crx'], new_task.command)

        # Restart once again
        newer_task = self.wfi.restart_task(new_task, test_checkpoint_file)

        # Assert inequality of Task objects
        self.assertNotEqual(new_task.id, newer_task.id)
        self.assertEqual("test_task-2", newer_task.name)

        # Assert equality of graph database objects
        self.assertEqual(newer_task, self.wfi.get_task_by_id(newer_task.id))
        self.assertEqual("RESTARTED", self.wfi.get_task_state(new_task.id))
        self.assertEqual("READY", self.wfi.get_task_state(newer_task.id))
        self.assertEqual(self.wfi.get_task_metadata(new_task.id),
                         self.wfi.get_task_metadata(newer_task.id))

        # Restart on more time (should return None)
        self.assertIsNone(self.wfi.restart_task(newer_task, test_checkpoint_file))

        # Check that task command includes checkpoint file
        self.assertListEqual(['ls', '-a', '-F', '-l', 'input.txt', '-R',
                              '/backup0.crx'], newer_task.command)

    def test_finalize_task(self):
        """Test finalization of completed tasks."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        tasks = self._create_test_tasks(workflow_id)
        self.wfi.execute_workflow()
        self.wfi.set_task_output(tasks[0].id, "prep/prep_output", "prep_output.txt")
        ready_tasks = self.wfi.finalize_task(tasks[0])

        # Manually set expected task input values for comparison
        tasks[1].inputs = [StepInput(id="input_data", type="File", value="prep_output.txt", default=None,
                                     source="prep/prep_output", prefix=None, position=None, value_from=None)]
        tasks[2].inputs = [StepInput(id="input_data", type="File", value="prep_output.txt", default=None,
                                     source="prep/prep_output", prefix=None, position=None, value_from=None)]
        tasks[3].inputs = [StepInput(id="input_data", type="File", value="prep_output.txt", default=None,
                                     source="prep/prep_output", prefix=None, position=None, value_from=None)]

        self.assertCountEqual(tasks[1:4], ready_tasks)

    def test_get_task_by_id(self):
        """Test obtaining a task from the graph database by its ID."""
        task_name = "test_task"
        base_command = "ls"
        inputs = [StepInput(id="input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None, value_from=None)]
        outputs = [StepOutput(id="test_task/test_task_done", type="stdout", value="output.txt", glob="output.txt")]
        requirements = [Requirement(class_="ResourceRequirement", params={"ramMin": 1024}),
                        Requirement(class_="NetworkAccess", params={"networkAccess": True})]
        hints = [Hint(class_="ResourceRequirement", params={"ramMin": 1024}),
                 Hint(class_="NetworkAccess", params={"networkAccess": True})]
        stdout = "output.txt"
        stderr = "output-err.txt"

        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/test_task_done")],
            id=workflow_id))

        task = Task(
            name=task_name,
            base_command=base_command,
            hints=hints,
            requirements=requirements,
            inputs=inputs,
            outputs=outputs,
            stdout=stdout,
            stderr=stderr,
            workflow_id=workflow_id)

        self.wfi.add_task(task)

        self.assertEqual(task, self.wfi.get_task_by_id(task.id))

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        requirements = [Requirement(class_="ResourceRequirement", params={"ramMin": 1024})]
        hints = [Hint(class_="NetworkAccess", params={"networkAccess": True})]
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=hints, requirements=requirements,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        tasks = self._create_test_tasks(workflow_id)

        (workflow, wf_tasks) = self.wfi.get_workflow()

        self.assertCountEqual(tasks, wf_tasks)
        self.assertCountEqual(requirements, workflow.requirements)
        self.assertCountEqual(hints, workflow.hints)

    def test_get_workflow_outputs(self):
        """Test obtaining the outputs of a workflow."""
        workflow = Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/test_task_done")],
            id=generate_workflow_id())
        self.wfi.initialize_workflow(workflow)

        self.assertListEqual(workflow.outputs, self.wfi.get_workflow_outputs())

    def test_get_workflow_state(self):
        """Test obtaining the state of a workflow."""
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/test_task_done")],
            id=generate_workflow_id()))

        # Initialized workflow state should be 'SUBMITTED'
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

        self.wfi.execute_workflow()

        # Executed workflow state should be 'RUNNING'
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_set_workflow_state(self):
        """Test setting the state of a workflow."""
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/test_task_done")],
            id=generate_workflow_id()))

        # Initialized workflow state should be 'SUBMITTED'
        self.assertEqual("SUBMITTED", self.wfi.get_workflow_state())

        self.wfi.set_workflow_state("RUNNING")

        # Workflow state should now be 'RUNNING'
        self.assertEqual("RUNNING", self.wfi.get_workflow_state())

    def test_get_ready_tasks(self):
        """Test obtaining of ready workflow tasks."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        tasks = self._create_test_tasks(workflow_id)

        # Should be no ready tasks
        self.assertListEqual([], self.wfi.get_ready_tasks())

        # Set Compute tasks to READY
        for task in tasks[1:4]:
            self.wfi.set_task_state(task.id, "READY")

        self.assertCountEqual(tasks[1:4], self.wfi.get_ready_tasks())

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="viz/output")],
            id=workflow_id))
        tasks = self._create_test_tasks(workflow_id)
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wfi.get_dependent_tasks(tasks[0].id)

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertCountEqual(tasks[1:4], dependent_tasks)

    def test_get_task_state(self):
        """Test obtaining of task state."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None,
                       value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        # Should be WAITING
        self.assertEqual("WAITING", self.wfi.get_task_state(task.id))

    def test_set_task_state(self):
        """Test the setting of task state."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None,
                       value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)

        self.wfi.add_task(task)

        self.wfi.set_task_state(task.id, "RUNNING")

        # Should now be RUNNING
        self.assertEqual("RUNNING", self.wfi.get_task_state(task.id))

    def test_get_task_metadata(self):
        """Test the obtaining of task metadata."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None,
                       value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        self.wfi.set_task_metadata(task.id, metadata)
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task.id))

    def test_set_task_metadata(self):
        """Test the setting of task metadata."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None,
                       value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)
        metadata = {"cluster": "fog", "crt": "charliecloud",
                    "container_md5": "67df538c1b6893f4276d10b2af34ccfe", "job_id": 1337}

        # Metadata should be empty
        self.assertDictEqual({}, self.wfi.get_task_metadata(task.id))

        self.wfi.set_task_metadata(task.id, metadata)

        # Metadata should now be populated
        self.assertDictEqual(metadata, self.wfi.get_task_metadata(task.id))

    def test_get_task_input(self):
        """Test the obtaining of a task input."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None,
                       value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        self.assertEqual(task.inputs[0], self.wfi.get_task_input(task.id, "test_input"))

    def test_set_task_input(self):
        """Test the setting of a task input."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value=None, default="default.txt", source="test_input", prefix=None, position=None, value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        test_input = StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input",
                               prefix=None, position=None, value_from=None)
        self.wfi.set_task_input(task.id, "test_input", "input.txt")
        self.assertEqual(test_input, self.wfi.get_task_input(task.id, "test_input"))

    def test_get_task_output(self):
        """Test the obtaining of a task output."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None, value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        self.assertEqual(task.outputs[0], self.wfi.get_task_output(task.id, "test_task/output"))

    def test_set_task_output(self):
        """Test the setting of a task output."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None, value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value=None, glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        test_output = StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")
        self.wfi.set_task_output(task.id, "test_task/output", "output.txt")
        self.assertEqual(test_output, self.wfi.get_task_output(task.id, "test_task/output"))

    def test_workflow_completed(self):
        """Test determining if a workflow has completed."""
        workflow_id = generate_workflow_id()
        self.wfi.initialize_workflow(Workflow(
            name="test_workflow", hints=None, requirements=None,
            inputs=[InputParameter(id="test_input", type="File", value="input.txt")],
            outputs=[OutputParameter(id="test_output", type="File", value="output.txt", source="test_task/output")],
            id=workflow_id))
        task = Task(
            name="test_task", base_command="ls", hints=None, requirements=None,
            inputs=[StepInput(id="test_input", type="File", value="input.txt", default="default.txt", source="test_input", prefix=None, position=None, value_from=None)],
            outputs=[StepOutput(id="test_task/output", type="File", value="output.txt", glob="output.txt")],
            stdout=None, stderr=None, workflow_id=workflow_id)
        self.wfi.add_task(task)

        # Workflow not completed
        self.assertFalse(self.wfi.workflow_completed())

        # Not using finalize_task() to avoid unnecessary queries
        self.wfi.set_task_state(task.id, 'COMPLETED')

        # Workflow now completed
        self.assertTrue(self.wfi.workflow_completed())

    def _create_test_tasks(self, workflow_id):
        """Create test tasks to reduce redundancy."""
        # Remember that add_task uploads the task to the database as well as returns a Task
        tasks = [
            Task(
                name="data_prep", base_command=["ls", "-a", "-F"],
                hints=[Hint(class_="ResourceRequirement", params={"ramMax": 2048})],
                requirements=[Requirement(class_="NetworkAccess", params={"networkAccess": True})],
                inputs=[StepInput(id="test_input", type="File", value=None, default=None, source="test_input", prefix="-l", position=None, value_from=None)],
                outputs=[StepOutput(id="prep/prep_output", type="File", value="prep_output.txt", glob="prep_output.txt")],
                stdout="prep_output.txt", stderr=None,
                workflow_id=workflow_id),
            Task(
                name="compute0", base_command="touch",
                hints=[Hint(class_="ResourceRequirement", params={"ramMax": 2048})],
                requirements=[Requirement(class_="NetworkAccess", params={"networkAccess": True})],
                inputs=[StepInput(id="input_data", type="File", value=None, default=None, source="prep/prep_output", prefix=None, position=None, value_from=None)],
                outputs=[StepOutput(id="compute0/output", type="File", value="output0.txt", glob="output0.txt")],
                stdout="output0.txt", stderr=None,
                workflow_id=workflow_id),
            Task(
                name="compute1", base_command="find",
                hints=[Hint(class_="ResourceRequirement", params={"ramMax": 2048})],
                requirements=[Requirement(class_="NetworkAccess", params={"networkAccess": True})],
                inputs=[StepInput(id="input_data", type="File", value=None, default=None, source="prep/prep_output", prefix=None, position=None, value_from=None)],
                outputs=[StepOutput(id="compute1/output", type="File", value="output1.txt", glob="output1.txt")],
                stdout="output1.txt", stderr=None,
                workflow_id=workflow_id),
            Task(
                name="compute2", base_command="grep",
                hints=[Hint(class_="ResourceRequirement", params={"ramMax": 2048})],
                requirements=[Requirement(class_="NetworkAccess", params={"networkAccess": True})],
                inputs=[StepInput(id="input_data", type="File", value=None, default=None, source="prep/prep_output", prefix=None, position=None, value_from=None)],
                outputs=[StepOutput(id="compute2/output", type="File", value="output2.txt", glob="output2.txt")],
                stdout="output2.txt", stderr=None,
                workflow_id=workflow_id),
            Task(
                name="visualization", base_command="python",
                hints=[Hint(class_="ResourceRequirement", params={"ramMax": 2048})],
                requirements=[Requirement(class_="NetworkAccess", params={"networkAccess": True})],
                inputs=[StepInput(id="input0", type="File", value=None, default=None, source="compute0/output", prefix="-i", position=1, value_from=None),
                        StepInput(id="input1", type="File", value=None, default=None, source="compute1/output", prefix="-i", position=2, value_from=None),
                        StepInput(id="input2", type="File", value=None, default=None, source="compute2/output", prefix="-i", position=3, value_from=None)],
                outputs=[StepOutput(id="viz/output", type="File", value="viz_output.txt", glob="viz_output.txt")],
                stdout="viz_output.txt", stderr=None,
                workflow_id=workflow_id)
        ]

        for task in tasks:
            self.wfi.add_task(task)

        return tasks


if __name__ == "__main__":
    unittest.main()
