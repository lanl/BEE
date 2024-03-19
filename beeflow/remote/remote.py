
"""remote_manager.py
This script manages an API that allows the remote submission and viewing of jobs, and Beeflow's state
"""


from beeflow.common import cli_connection
from beeflow.common import paths

from fastapi import FastAPI
import sys
import os
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    """Get Connection info"""
    #Update this root endpoint with a very brief documentation of the various other endpoints.
    return {"Endpoint info": 
            """
            You have reached the beeflow core API.
            Detailed documentation is available here: https://lanl.github.io/BEE/
            The following endpoints are available:
            /core/status: Get status information about all of the core beeflow components
            """
            }

@app.get("/workflows/status/{wfid}")
def get_wf_status(wfid: str):
    #TODO
    pass

@app.get("/droppoint")
def get_drop_point():
    """ Transmit the scp location to be used for the storage of workflow tarballs """
    return paths.droppoint_root()
    

@app.get("/owner")
def get_owner():
    """ Transmit the owner of this beeflow instance """
    user_name = os.getenv('USER') or os.getenv('USERNAME')
    return user_name


@app.get("/submit/{filename}")
def submit_new_wf(filename: str):
    """Submit a new workflow with a tarball for the workflow at a given path"""
    #TODO How are we going to get the workflow tarball onto the instance?
    pass


@app.get("/cleanup")
def cleanup_wf_directory():
    """Delete all the temporarily stored workflow tarballs"""
    #TODO
    pass

@app.get("/core/status/")
def get_core_status():
    """Check the status of beeflow and the components."""
    output = {}
    resp = cli_connection.send(paths.beeflow_socket(), {'type': 'status'})
    if resp is None:
        beeflow_log = paths.log_fname('beeflow')
        output["error"] = 'Cannot connect to the beeflow daemon, is it running?'
        return output
    for comp, stat in resp['components'].items():
        output[comp] = stat
    return output

def create_app():
    """ Start the web-server for the API with uvicorn """
    #TODO decide what port we're using for the long term. I set it to port 7777 temporarily
    uvicorn.run("beeflow.remote.remote:app", host="0.0.0.0", port=7777, reload=True)
