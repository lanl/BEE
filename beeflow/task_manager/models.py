from pydantic import BaseModel
from beeflow.common.object_models import Task

class SubmitTasksRequest(BaseModel):
    tasks: list[Task]

class TaskActionResponse(BaseModel):
    msg: str

