#! /usr/bin/env python3
"""Unit test for Neo4j driver."""

import unittest

import beeflow.common.bee_wf as wf_interface


class WFInterfaceTest(unittest.TestCase):
    """Unit test case for the workflow interface."""
    def test_neo4j_():
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

        wf_interface.create_workflow(tasks)


if __name__ == "__main__":
    unittest.main()
