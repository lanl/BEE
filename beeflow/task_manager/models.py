"""Models for task management in Beeflow."""
from pydantic import BaseModel
from beeflow.common.object_models import Task

class SubmitTasksRequest(BaseModel):
    """Request model for submitting tasks."""
    tasks: list[Task]

class TaskActionResponse(BaseModel):
    """Response model for task actions."""
    msg: str
