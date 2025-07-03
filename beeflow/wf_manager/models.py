from pydantic import BaseModel
from typing import Optional, List
from beeflow.common.object_models import Workflow, Task

class WorkflowInfo(BaseModel):
    """Information about a workflow."""
    wf_id: str
    wf_name: str
    wf_status: str

class ListWorkflowsResponse(BaseModel):
    """Response model for listing workflows."""
    workflow_info_list: list[WorkflowInfo]

class SubmitWorkflowRequest(BaseModel):
    """Request model for submitting a workflow."""
    wf_name: str
    wf_filename: str
    wf_workdir: str
    no_start: bool
    workflow: Workflow
    tasks: list[Task]
    encoded_tarball: Optional[str] = None

class SubmitWorkflowResponse(BaseModel):
    """Response model for workflow submission."""
    msg: str
    status: str
    wf_id: Optional[str] = None


class TaskStateUpdate(BaseModel):
    """Information about a task state update."""
    wf_id: str
    task_id: str
    job_state: str
    task_info: Optional[dict] = None
    output: Optional[dict] = None
    metadata: Optional[dict] = None


class TaskStateUpdateRequest(BaseModel):
    """Request model for Task State Update."""
    state_updates: List[TaskStateUpdate]


class TaskStateUpdateResponse(BaseModel):
    """Response model for Task State Update."""
    status: str

class ModifyWorkflowRequest(BaseModel):
    """Request model for modifying a workflow."""
    option: str

class WorkflowActionResponse(BaseModel):
    """Response model for workflow actions."""
    msg: str

class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status."""
    tasks_status: List[tuple]
    wf_status: str
    status: str
