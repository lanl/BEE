"""Scheduler types for storing scheduling information.

This file holds classes for respresenting workflows and tasks/jobs, as
well as resources that will be used during scheduling.
"""
from pydantic import BaseModel
from typing import Optional


class SchedulerRequirements(BaseModel):
    """Requirements class."""
    max_runtime: int
    nodes: Optional[int] = 1
    mem_per_node: Optional[int] = 1024
    gpus_per_node: Optional[int] = 0
    cost: Optional[float] = 1.0


class Allocation(BaseModel):
    id_: str
    start_time: int
    max_runtime: int
    nodes: int


class SchedulerTask(BaseModel):
    """Representation of a Task and its various requirements.

    This class represents the task as a set of resource requirements
    which can be used by the scheduling algorithm to easily determine
    the best allocation.
    """
    workflow_name: str
    task_name: str
    requirements: Optional[SchedulerRequirements] = SchedulerRequirements(max_runtime=1)
    allocations: Optional[list[Allocation]] = []


class ScheduleTasksRequest(BaseModel):
    """Request for scheduling tasks"""
    tasks: list[SchedulerTask]

class ScheduleTasksResponse(BaseModel):
    """Response for scheduling tasks"""
    tasks: list[SchedulerTask]



