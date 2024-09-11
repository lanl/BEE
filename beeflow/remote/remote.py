"""This script manages an API that allows the remote submission of jobs."""
import os
import socket
import pathlib
from fastapi import FastAPI
import uvicorn

from beeflow.common import cli_connection
from beeflow.common import paths
from beeflow.client import bee_client
from beeflow.common.config_driver import BeeConfig as bc


app = FastAPI()


@app.get("/")
def read_root():
    """Get REST Connection info."""
    return {"Endpoint info": "BEEflow core API: Documentation - https://lanl.github.io/BEE/"}


@app.get("/workflows/status/")
def get_wf_status():
    """WIP - This endpoint is planned to give you a status on an actively running workflow."""


@app.get("/droppoint")
def get_drop_point():
    """Transmit the scp location to be used for the storage of workflow tarballs.

    Users are required to ensure that this directory has the appropriate permissions.
    """
    output = {}
    output["droppoint"] = str(paths.droppoint_root())
    return output


@app.get("/owner")
def get_owner():
    """Transmit the owner of this BEEflow instance."""
    user_name = os.getenv('USER') or os.getenv('USERNAME')
    return user_name


@app.get("/submit/{filename}")
def submit_new_wf(filename: str):
    """WIP: Submit a new workflow with a tarball for the workflow at a given path."""
    return filename


@app.get("/submit_long/{wf_name}/{tarball_name}/{main_cwl_file}/{job_file}")
def submit_new_wf_long(wf_name: str, tarball_name: str, main_cwl_file: str, job_file: str):
    r"""Submit a new workflow with a tarball for the workflow at a given path.

    This makes the following assumptions:\n
    The workflow tarball should be at <DROPPOINT_PATH>/<tarball name>\n
    The workdir should be at <DROPPOINT_PATH>/<tarball name>-workdir and
    should have the required input files.
    """
    output = {}
    # Append the droppoint path to the tarball_name
    workflow_path = paths.droppoint_root() + "/" + tarball_name
    # Make a workdir path
    workdir_path = paths.droppoint_root() + "/" + tarball_name.replace(".tgz", "") + "-workdir"
    # Make sure that the directory exists, if not create it with owner-only permissions
    if not os.path.exists(workdir_path):
        os.makedirs(workdir_path, mode=0o700)

    # Validate the path to the tarball.
    if not os.path.exists(workflow_path):
        output["error"] = "The workflow tarball name provided was not found in the drop point."
        return output

    # Convert the paths to pathlib paths.
    workflow_path = pathlib.Path(workflow_path)
    workdir_path = pathlib.Path(workdir_path)

    try:
        bee_client.submit(wf_name,
                          workflow_path,
                          main_cwl_file,
                          job_file,
                          workdir_path,
                          no_start=False)
        output["result"] = "Submitted new workflow" + str(wf_name)
        return output
    except bee_client.ClientError as error:
        output["error"] = str(error)
        return output


@app.get("/showdrops")
def show_drops():
    """WIP: This endpoint will give a list of workflows in the droppoint."""


@app.get("/cleanup")
def cleanup_wf_directory():
    """WIP: This endpoint is planned to delete all the temporarily stored workflow tarballs."""


@app.get("/core/status/")
def get_core_status():
    """Check the status of BEEflow and the components."""
    output = {}
    resp = cli_connection.send(paths.beeflow_socket(), {'type': 'status'})
    if resp is None:
        output["error"] = 'Cannot connect to the beeflow daemon, is it running?'
        return output
    for comp, stat in resp['components'].items():
        output[comp] = stat
    return output


def is_port_taken(port, host='127.0.0.1'):
    """Check if a port is in use on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
        except socket.error:
            return True  # Port is taken
    return False  # Port is free


def find_free_port(start_port=1024, end_port=65535, host='127.0.0.1'):
    """Search for a free port within the given range."""
    for port in range(start_port, end_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port  # Return the first free port found
            except socket.error:
                continue  # If the port is in use, try the next one
    raise RuntimeError(f"No free port found in range {start_port}-{end_port}")


def create_app():
    """Start the web-server for the API with uvicorn."""
    # decide what port we're using for the long term. I set it to port 7777 temporarily

    port_number = bc.get('DEFAULT', 'remote_api_port')
    if is_port_taken(port_number) is True:
        print("Requested port number is unavailable, attempting to map port dynamically")

        port_number = find_free_port()
        print(f"Available port found: {port_number}")

    config = uvicorn.Config("beeflow.remote.remote:app",
                            host="0.0.0.0",
                            port=port_number,
                            reload=True,
                            log_level="info")
    server = uvicorn.Server(config)

    try:
        server.run()
    except OSError as exception:
        if exception.errno == 98:
            print(f"Selected port {port_number} is already in use.")
        raise
