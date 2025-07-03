from pydantic import BaseModel
from typing import Optional
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
