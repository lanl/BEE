
"""remote_manager.py
This script manages an API that allows the remote submission and viewing of jobs, and Beeflow's state
"""


from fastapi import FastAPI
from beeflow.common import cli_connection
from beeflow.common import paths

import sys
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    """Get Connection info"""
    #TODO
    return {"Hello": "World"}

@app.get("/workflows/status/{wfid}")
def get_wf_status(wfid: str):
    #TODO
    pass

@app.get("/submit/{filename}")
def submit_new_wf(filename: str):
    """Submit a new workflow with a tarball for the workflow at a given path"""
    #TODO How are we going to get the workflow tarball onto the instance?
    pass

@app.get("/upload/{file}")
def upload_tarball(file: str):
    """Upload a tarball file"""
    #TODO We might need to do this in pieces if the file is really big. Lets see if FASTAPI already has something for that
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
    #TODO decide what port we're using for the long term. I set it to port 7777 temporarily because I thought it would be 
    #funny if we showed up on nmap scans by our OPFOR as a terraria server. This port only seems to be used by various video games
    #according to the references I found so it might be ideal for HPC purposes.
    uvicorn.run("beeflow.remote.remote:app", host="127.0.0.1", port=7777, reload=True)
