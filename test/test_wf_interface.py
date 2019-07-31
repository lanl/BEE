#! /usr/bin/env python3
"""Unit test module for the BEE workflow interface module."""

# Disable protected member access warning
# pylama:ignore=W0212

import unittest

from beeflow.common import wf_interface


class TestWFInterface(unittest.TestCase):
    """Unit test case for the workflow interface."""

    def tearDown(self):
        """Clear all data in the Neo4j database."""
        wf_interface._GDB_INTERFACE.cleanup()

    def test_create_task(self):
        """Test task creation."""
        task_name = "Test Task"
        commands = [["ls", "-a", "-l", "-F"]]
        requirements = {"ram": 1024, "cores": 4}
        hints = {"cpus": 2}
        subworkflow = "Test Subworkflow"
        inputs = {"input1.txt", "input2.txt"}
        outputs = {"test_task_done"}

        task = wf_interface.create_task(
            name=task_name,
            commands=commands,
            requirements=requirements,
            hints=hints,
            subworkflow=subworkflow,
            inputs=inputs,
            outputs=outputs)

        # Task assertions
        self.assertEqual(task_name, task.name)
        self.assertListEqual(commands, task.commands)
        self.assertEqual(requirements, task.requirements)
        self.assertEqual(hints, task.hints)
        self.assertEqual(subworkflow, task.subworkflow)
        self.assertEqual(inputs, task.inputs)
        self.assertEqual(outputs, task.outputs)

    def test_create_workflow_auto(self):
        """Test workflow creation.

        Creation of bee_init and bee_exit is automatic.
        """
        tasks = _create_test_tasks(bee_nodes=False)
        requirements = {"ranks": 128}
        hints = {"cluster": "badger"}

        workflow = wf_interface.create_workflow(
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
        tasks = _create_test_tasks()
        requirements = {"ranks": 128}
        hints = {"cluster": "badger"}

        workflow = wf_interface.create_workflow(
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
        tasks = _create_test_tasks()

        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)

        # Test task states
        for task in tasks:
            self.assertEqual("WAITING", wf_interface.get_task_state(task))

    def test_get_subworkflow(self):
        """Test obtaining of a subworkflow."""
        # Create a workflow without bee_init, bee_exit
        tasks = _create_test_tasks(bee_nodes=False)
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)

        # Subworkflow assertion
        for i in range(1, 4):
            self.assertEqual(tasks[i], wf_interface.get_subworkflow(
                "Compute", workflow.requirements, workflow.hints)[tasks[i].id])

    def test_finalize_workflow(self):
        """Test workflow finalization."""
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        wf_interface.finalize_workflow()

        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[0]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[1]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[2]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[3]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[4]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[5]))
        self.assertEqual("READY", wf_interface.get_task_state(tasks[6]))

    def test_initialize_workflow(self):
        """Test workflow initialization.

        The bee_init node should have its state set from "WAITING" to "READY"
        """
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        wf_interface.initialize_workflow()

        self.assertEqual("READY", wf_interface.get_task_state(tasks[0]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[1]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[2]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[3]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[4]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[5]))
        self.assertEqual("WAITING", wf_interface.get_task_state(tasks[6]))

    def test_get_dependent_tasks(self):
        """Test obtaining of dependent tasks."""
        # Create a workflow without bee_init, bee_exit
        tasks = _create_test_tasks(bee_nodes=False)
        workflow = wf_interface.create_workflow(tasks)
        wf_interface.load_workflow(workflow)
        # Get dependent tasks of Data Prep
        dependent_tasks = wf_interface.get_dependent_tasks(tasks[0])

        # Should equal Compute 0, Compute 1, and Compute 2
        self.assertSetEqual(set(tasks[1:4]), dependent_tasks)

    def test_get_task_state(self):
        """Test obtaining of task status."""
        task = wf_interface.create_task("Test Task")
        workflow = wf_interface.create_workflow([task])
        wf_interface.load_workflow(workflow)

        # Should be WAITING because workflow not initialized
        self.assertEqual("WAITING", wf_interface.get_task_state(task))

    def test_workflow_loaded(self):
        """Test determining if a workflow is loaded."""
        tasks = _create_test_tasks()
        workflow = wf_interface.create_workflow(tasks)

        # No workflow loaded
        self.assertFalse(wf_interface.workflow_loaded())

        wf_interface.load_workflow(workflow)

        # Workflow now loaded
        self.assertTrue(wf_interface.workflow_loaded())


def _create_test_tasks(bee_nodes=True):
    """Create test tasks to reduce redundancy.

    :param bee_nodes: flag to add bee_init and bee_exit tasks
    :type bee_nodes: boolean
    """
    if bee_nodes:
        # Create workflow with bee_init and bee_exit tasks
        tasks = [
            wf_interface.create_task("bee_init", inputs={"input.txt"}, outputs={"input.txt"}),
            wf_interface.create_task("Data Prep", commands=[["ls", "-a", "-l", "-F"]],
                                     requirements={"ram": 64, "cores": 4}, hints={"cpus": 2},
                                     inputs={"input.txt"}, outputs={"prep_input.txt"}),
            wf_interface.create_task("Compute 0", commands=[["rm", "-r", "-f"], ["touch"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output1.txt"}),
            wf_interface.create_task("Compute 1", commands=[["find"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output2.txt"}),
            wf_interface.create_task("Compute 2", commands=[["yes"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output3.txt"}),
            wf_interface.create_task("Visualization", commands=[["ln", "-s"]],
                                     requirements={"ram": 128, "cores": 8}, hints={"cpus": 2},
                                     inputs={"output1.txt", "output2.txt", "output3.txt"},
                                     outputs={"output.txt"}),
            wf_interface.create_task("bee_exit",
                                     inputs={"output.txt"},
                                     outputs={"output.txt"})
        ]
    else:
        # Do not create bee_init and bee_exit
        tasks = [
            wf_interface.create_task("Data Prep", commands=[["ls", "-a", "-l", "-F"]],
                                     requirements={"ram": 64, "cores": 4}, hints={"cpus": 2},
                                     inputs={"input.txt"}, outputs={"prep_input.txt"}),
            wf_interface.create_task("Compute 0", commands=[["rm", "-r", "-f"], ["touch"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output1.txt"}),
            wf_interface.create_task("Compute 1", commands=[["find"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output2.txt"}),
            wf_interface.create_task("Compute 2", commands=[["yes"]],
                                     requirements={"ram": 128, "cores": 4}, hints={"cpus": 2},
                                     subworkflow="Compute", inputs={"prep_input.txt"},
                                     outputs={"output3.txt"}),
            wf_interface.create_task("Visualization", commands=[["ln", "-s"]],
                                     requirements={"ram": 128, "cores": 8}, hints={"cpus": 2},
                                     inputs={"output1.txt", "output2.txt", "output3.txt"},
                                     outputs={"output.txt"}),
        ]

    return tasks


if __name__ == "__main__":
    unittest.main()
