from pydantic import BaseModel
from typing import Optional
from beeflow.common.object_models import Workflow, Task

class SubmitWorkflowRequest(BaseModel):
    """Request model for submitting a workflow."""
    wf_name: str
    wf_filename: str
    wf_workdir: str
    no_start: bool
    workflow: Workflow
    tasks: list[Task]
    encoded_tarball: Optional[str] = None