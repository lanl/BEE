#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

from beeflow.common.wf_interface import WorkflowInterface


class TestWorkflowInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    @classmethod
    def setUpClass(cls):
        """Initialize the Workflow interface."""
        cls.wf = WorkflowInterface()

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        self.wf.unload_workflow()

    def test_create_task(self):
        """Test task creation."""
        task_name = "Test Task"
        command = ["ls", "-a", "-l", "-F"]
        hints = {self.wf.create_requirement("ResourceRequirement", "ramMin", 1024),
                 self.wf.create_requirement("NetworkAccess", "networkAccess", True)}
        subworkflow = "Test Subworkflow"
        inputs = {"input1.txt", "input2.txt"}
        outputs = {"test_task_done"}

        task = self.wf.create_task(
            name=task_name,
            command=command,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        # Task assertions
        self.assertEqual(task_name, task.name)
        self.assertListEqual(command, task.command)
        self.assertEqual(hints, task.hints)
        self.assertEqual(subworkflow, task.subworkflow)
        self.assertEqual(inputs, task.inputs)
        self.assertEqual(outputs, task.outputs)

    def test_create_requirement(self):
        """Test workflow requirement creation."""
        req_class = "ResourceRequirement"
        req_key = "ramMin"
        req_value = 1024

        req = self.wf.create_requirement(req_class, req_key, req_value)

        self.assertEqual(req_class, req.req_class)
        self.assertEqual(req_key, req.key)
        self.assertEqual(req_value, req.value)

    def test_create_workflow_auto(self):
        """Test workflow creation.

        Creation of bee_init and bee_exit is automatic.
        """
        tasks = self._create_test_tasks(bee_nodes=False)
        requirements = {self.wf.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wf.create_requirement("NetworkAccess", "networkAccess", True)}

        workflow = self.wf.create_workflow(
            tasks=tasks,
            requirements=requirements,
            hints=hints)

        # Test Workflow object population
        self.assertSetEqual(set(tasks), workflow.tasks)
        self.assertEqual(requirements, workflow.requirements)
        self.assertEqual(hints, workflow.hints)

        # Test automatic Task ID assignment
        # Task IDs should be strictly incremental
        first_task_id = tasks[0].id
        for task_id, task in enumerate(tasks, start=first_task_id):
            self.assertEqual(task_id, task.id)

        # Test automatic dependency assignment
        self.assertSetEqual({tasks[5].id}, workflow._tasks[tasks[0].id].dependencies)
        self.assertSetEqual({tasks[0].id}, workflow._tasks[tasks[1].id].dependencies)
        self.assertSetEqual({tasks[0].id}, workflow._tasks[tasks[2].id].dependencies)
        self.assertSetEqual({tasks[0].id}, workflow._tasks[tasks[3].id].dependencies)
        self.assertSetEqual({tasks[1].id, tasks[2].id, tasks[3].id},
                            workflow._tasks[tasks[4].id].dependencies)
        self.assertSetEqual({tasks[4].id}, workflow._tasks[tasks[6].id].dependencies)

    def test_create_workflow_manual(self):
        """Test workflow creation.

        Creation of bee_init and bee_exit is manual.
        """
        tasks = self._create_test_tasks()
        requirements = {self.wf.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wf.create_requirement("NetworkAccess", "networkAccess", True)}

        workflow = self.wf.create_workflow(
            tasks=tasks,
            requirements=requirements,
            hints=hints)

        # Test Workflow object population
        self.assertSetEqual(set(tasks), workflow.tasks)
        self.assertEqual(requirements, workflow.requirements)
        self.assertEqual(hints, workflow.hints)

        # Test automatic Task ID assignment
        # Task IDs should be strictly incremental
        first_task_id = tasks[0].id
        for task_id, task in enumerate(tasks, start=first_task_id):
            self.assertEqual(task_id, task.id)

        # Test automatic dependency assignment
        self.assertSetEqual({tasks[0].id}, workflow._tasks[tasks[1].id].dependencies)
        self.assertSetEqual({tasks[1].id}, workflow._tasks[tasks[2].id].dependencies)
        self.assertSetEqual({tasks[1].id}, workflow._tasks[tasks[3].id].dependencies)
        self.assertSetEqual({tasks[1].id}, workflow._tasks[tasks[4].id].dependencies)
        self.assertSetEqual({tasks[2].id, tasks[3].id, tasks[4].id},
                            workflow._tasks[tasks[5].id].dependencies)
        self.assertSetEqual({tasks[5].id}, workflow._tasks[tasks[6].id].dependencies)

    def test_load_workflow(self):
        """Test workflow insertion into the graph database."""
        tasks = self._create_test_tasks(False)

        workflow = self.wf.create_workflow(
            tasks=tasks,
            requirements={self.wf.create_requirement("ResourceRequirement", "ramMin", 1024)},
            hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)})
        self.wf.load_workflow(workflow)

        self.assertTrue(self.wf.workflow_loaded())

        # Test task states
        for task in tasks:
            self.assertEqual("WAITING", self.wf.get_task_state(task))

        self.assertEqual(workflow, self.wf.get_workflow())

    def test_unload_workflow(self):
        """Test workflow deletion from the graph database."""
        tasks = self._create_test_tasks()

        workflow = self.wf.create_workflow(tasks)
        self.wf.load_workflow(workflow)

        self.wf.unload_workflow()

        self.assertFalse(self.wf.workflow_loaded())

    def test_get_workflow(self):
        """Test obtaining the workflow from the graph database."""
        tasks = self._create_test_tasks()
        requirements = {self.wf.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wf.create_requirement("NetworkAccess", "networkAccess", True)}

        workflow = self.wf.create_workflow(tasks, requirements, hints)
        self.wf.load_workflow(workflow)

        self.assertTrue(self.wf.workflow_loaded())
        self.assertEqual(workflow, self.wf.get_workflow())

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        # Create a workflow without bee_init, bee_exit
        tasks = self._create_test_tasks()
        requirements = {self.wf.create_requirement("ResourceRequirement", "ramMin", 1024)}
        hints = {self.wf.create_requirement("NetworkAccess", "networkAccess", True)}

        workflow = self.wf.create_workflow(tasks, requirements, hints)
        self.wf.load_workflow(workflow)

        # Subworkflow assertion
        self.assertEqual(self.wf.create_workflow(tasks[2:5], requirements, hints),
                         self.wf.get_subworkflow("Compute"))

    def test_finalize_workflow(self):
        """Test workflow finalization."""
        tasks = self._create_test_tasks()
        workflow = self.wf.create_workflow(tasks)
        self.wf.load_workflow(workflow)
        self.wf.finalize_workflow()

        self.assertEqual("WAITING", self.wf.get_task_state(tasks[0]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[1]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[2]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[3]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[4]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[5]))
        self.assertEqual("READY", self.wf.get_task_state(tasks[6]))

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The bee_init node should have its state set from "WAITING" to "READY"
        """
        tasks = self._create_test_tasks()
        workflow = self.wf.create_workflow(tasks)
        self.wf.load_workflow(workflow)
        self.wf.initialize_workflow()

        self.assertEqual("READY", self.wf.get_task_state(tasks[0]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[1]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[2]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[3]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[4]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[5]))
        self.assertEqual("WAITING", self.wf.get_task_state(tasks[6]))

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        # Create a workflow without bee_init, bee_exit
        tasks = self._create_test_tasks()
        workflow = self.wf.create_workflow(tasks)
        self.wf.load_workflow(workflow)
        # Get dependent tasks of Data Prep
        dependent_tasks = self.wf.get_dependent_tasks(tasks[1])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertSetEqual(set(tasks[2:5]), set(dependent_tasks))

    def test_get_task_state(self):
        """Test obtaining of task status."""
        task = self.wf.create_task("Test Task")
        workflow = self.wf.create_workflow([task])
        self.wf.load_workflow(workflow)

        # Should be WAITING because workflow not initialized
        self.assertEqual("WAITING", self.wf.get_task_state(task))

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        tasks = self._create_test_tasks()
        workflow = self.wf.create_workflow(tasks)

        # No workflow loaded
        self.assertFalse(self.wf.workflow_loaded())

        self.wf.load_workflow(workflow)

        # Workflow now loaded
        self.assertTrue(self.wf.workflow_loaded())

    def _create_test_tasks(self, bee_nodes=True):
        """Create test tasks to reduce redundancy.

        :param bee_nodes: flag to add bee_init and bee_exit tasks
        :type bee_nodes: boolean
        """
        if bee_nodes:
            # Create workflow with bee_init and bee_exit tasks
            tasks = [
                self.wf.create_task("bee_init", inputs={"input.txt"}, outputs={"input.txt"}),
                self.wf.create_task(
                    "Data Prep", command=["ls", "-a", "-l", "-F"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    inputs={"input.txt"}, outputs={"prep_input.txt"}),
                self.wf.create_task(
                    "Compute 0", command=["rm", "-r", "-f"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output1.txt"}),
                self.wf.create_task(
                    "Compute 1", command=["find"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output2.txt"}),
                self.wf.create_task(
                    "Compute 2", command=["yes"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output3.txt"}),
                self.wf.create_task(
                    "Visualization", command=["ln", "-s"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 4096)},
                    inputs={"output1.txt", "output2.txt", "output3.txt"},
                    outputs={"output.txt"}),
                self.wf.create_task("bee_exit", inputs={"output.txt"}, outputs={"output.txt"})
            ]
        else:
            # Do not create bee_init and bee_exit
            tasks = [
                self.wf.create_task(
                    "Data Prep", command=["ls", "-a", "-l", "-F"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    inputs={"input.txt"}, outputs={"prep_input.txt"}),
                self.wf.create_task(
                    "Compute 0", command=["rm", "-r", "-f"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output1.txt"}),
                self.wf.create_task(
                    "Compute 1", command=["find"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output2.txt"}),
                self.wf.create_task(
                    "Compute 2", command=["yes"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 2048)},
                    subworkflow="Compute", inputs={"prep_input.txt"},
                    outputs={"output3.txt"}),
                self.wf.create_task(
                    "Visualization", command=["ln", "-s"],
                    hints={self.wf.create_requirement("ResourceRequirement", "ramMax", 4096)},
                    inputs={"output1.txt", "output2.txt", "output3.txt"},
                    outputs={"output.txt"}),
            ]
        return tasks


if __name__ == "__main__":
    unittest.main()
