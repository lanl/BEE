"""Tools and resources for the MCP BEE Server."""
import requests 
import io
import os
import subprocess
import logging
from typing import Optional, Union
from pathlib import Path
from contextlib import redirect_stdout
from beeflow.client import bee_client
from mcp.server.fastmcp import FastMCP 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("BEE")


class BeeError(Exception):
    """Base exception for beeflow related errors."""

    pass

class BeeParameterError(BeeError):
    """Errors associated with workflow parameters."""

    pass

class BeeWorkflowError(BeeError):
    """Workflow associated errors."""

    pass  

def find_workdir(workdir,source=Path.home()) -> Path:
    """Locates the working directory for the workflow"""
    workdir_path = Path(workdir).expanduser().resolve()
    if workdir_path.exists() and workdir_path.is_dir(): 
        logger.info(f"Successfully found the working directory path: {workdir_path}")
        return workdir_path
    
    try:
        result = subprocess.run(
                ["find",str(source),"-type","d","-name",workdir,"-print","-quit"],
                 capture_output=True,
                 text=True,
                 timeout=150
        )
        
        if result.stdout.strip():
            found_workdir_path = Path(result.stdout.strip())
            logger.info(f"Successfully found the working directory path: {found_workdir_path}")
            return found_workdir_path

        else:
            raise FileNotFoundError(f"Could not find directory '{workdir}' under {source}")

    except subprocess.TimeoutExpired:
        logger.exception(f"Could not find {workdir} in 150 seconds.")
        raise TimeoutError(f"Search for '{workdir}' under {source} timed out in 150 seconds.")


def validate_parameters(params: dict) -> None:
    """Check if any parameters are empty."""
    for param_name, param in params.items():
        if not param:
            raise BeeParameterError(f"Please include a value for: {param_name}")
    return None

@mcp.tool()
async def submit_workflow(wf_name: str, wf_path: str, main_cwl: str, yaml: str, 
        workdir: str, no_start: Optional[bool] = False) -> str:
    """Submits a workflow into BEE with the specified paramaters."""
    
    params = {"wf_name":wf_name.strip(), 
              "wf_path":wf_path.strip(), 
              "main_cwl": main_cwl.strip(),
              "yaml": yaml.strip(), 
              "workdir": workdir.strip()}
    
    validate_params = validate_parameters(params)

    workdir_path = find_workdir(workdir)
    logger.info(f"Working directory has been found...{workdir_path}")
    
    try: 
        submit_buffer = io.StringIO()
        with redirect_stdout(submit_buffer): # redirect any print statements that are polluting data stream read by client
            wf_id = bee_client.submit(wf_name,workdir_path/Path(wf_path),workdir_path/Path(main_cwl),
                                        workdir_path/Path(yaml),workdir_path,no_start)

        logger.info(f"===Workflow submitted with the following parameters===" \
                    f"workflow name: {wf_name}, "\
                    f"workflow path: {wf_path}, "\
                    f"main cwl file: {main_cwl}, "\
                    f"yaml file: {yaml}, "\
                    f"working directory: {workdir}")

        return f"Workflow submitted! Your workflow id is {wf_id}"
    except Exception as e:
        logger.exception(f"Could not successfully submit workflow with the following parameters: "\
                     f"{wf_name}, {wf_path}, {main_cwl}, {yaml}, {workdir}")

        raise BeeWorkflowError(f"Unable to successfully submit workflow: {e}")
    
@mcp.tool()
async def query_workflow(wf_id:str) -> str:
    """Get the status of a workflow."""
    
    param = {"wf_id": wf_id}
    validate_parameters(param)

    try:
        query_buffer = io.StringIO()
        with redirect_stdout(query_buffer):
            wf_status,_ = bee_client.query(wf_id)
            logger.info(f"Current status of your workflow: {wf_status}")
        
        task_info = query_buffer.getvalue()
        logger.info(f"Task(s) information: {task_info}")

        return f"Workflow status: {wf_status}"
    except Exception as e:
        raise BeeWorkflowError(f"Unable to successfully query workflow: {e}")

@mcp.tool()
async def cancel_workflow(wf_ids: Union[list[str],str,None] = None, all_flag: Optional[bool] = False) -> str:
    if not wf_ids:
        raise BeeParameterError(f"Enter one or more workflow ids or specify the 'all' keyword.")

    try:
        cancel_buffer = io.StringIO()
        with redirect_stdout(cancel_buffer):
            bee_client.cancel(wf_ids,all_flag)
            logger.info(f"Canceling workflow(s) successfully: {wf_ids}")
        
        return "Canceling workflow(s)..."
    except Exception as e:
        raise BeeWorkflowError(f"Unable to cancel workflow(s): {e}")

@mcp.tool()
async def list_workflows() -> str:
    """List all workflows"""

    try:
        list_buffer = io.StringIO()
        with redirect_stdout(list_buffer):
            bee_client.list_workflows()
            logger.info(f"Successfully listed workflows!")

        return f"Listing workflows...\n{list_buffer.getvalue()}"
    except Exception as e:
        raise BeeWorkflowError(f"Unable to list all workflows: {e}")

@mcp.resource("https://BEE/docs")
async def read_BEE():
    """Provide information regarding BEE"""
    
    docs_url = "https://lanl.github.io/BEE/"
    response = requests.get(docs_url)
    status_code = response.raise_for_status() # throws an HTTPError exception if unsuccessful
    logger.info(status_code)
    return response.text

if __name__ == "__main__":
    mcp.run(transport="stdio")

