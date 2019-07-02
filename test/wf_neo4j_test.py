#! /usr/bin/env python3
"""Unit test for Neo4j driver."""

import beeflow.common.bee_wf as wf_interface


def test():
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
            "viz", "Visualization", "sl",
            dependencies={"crank0", "crank1", "crank2"}))
    wf_interface.create_workflow(tasks)


if __name__ == "__main__":
    test()
