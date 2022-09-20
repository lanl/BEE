#!/usr/bin/env python3
"""bee-client.

This script provides an client interface to the user to manage workflows.
Capablities include submitting, starting, listing, pausing and cancelling workflows.
"""
import os
import sys
import logging
import inspect
import shutil
import pathlib
import subprocess
import jsonpickle
import requests
import typer
from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.cli import NaturalOrderGroup


# Length of a shortened workflow ID
short_id_len = 6 #noqa: Not a constant

# Maximum length of a workflow ID
MAX_ID_LEN = 32

# Global used to indicate whether this instance is interactive or not
_INTERACTIVE = False


logging.basicConfig(level=logging.WARNING)


class ClientError(Exception):
    """Client error class."""

    def __init__(self, *args):
        """Error constructor."""
        self.args = args


def error_exit(msg):
    """Raise error with message."""
    caller_func = str.capitalize(inspect.stack()[1].function)
    msg = caller_func + ': ' + msg
    if _INTERACTIVE:
        typer.secho(msg, fg=typer.colors.RED)
        sys.exit(1)
    else:
        # Raise an error so that client libraries can handle it
        raise ClientError(msg) from None


def _url():
    """Return URL to the workflow manager end point."""
    wfm_listen_port = bc.get('workflow_manager', 'listen_port')
    workflow_manager = 'bee_wfm/v1/jobs'
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'


def _short_id(wf_id):
    return wf_id[:short_id_len]


def _resource(tag=""):
    return _url() + str(tag)


def check_short_id_collision():
    """Check short workflow IDs for colliions; increase short ID length if detected."""
    global short_id_len  #noqa: Not a constant
    resp = requests.get(_url(), timeout=60)
    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit("Checking for ID collision failed: {resp.status_code}")

    workflow_list = jsonpickle.decode(resp.json()['workflow_list'])
    if workflow_list:
        while short_id_len < MAX_ID_LEN:
            id_list = [_short_id(job[1]) for job in workflow_list]
            id_list_set = set(id_list)
            # Collision if set shorter than list
            if len(id_list_set) < len(id_list):
                short_id_len += 1
            else:
                break
        else:
            raise RuntimeError("collision detected between two full workflow IDs")
    else:
        print("There are currently no jobs.")


def match_short_id(wf_id):
    """Match user-provided short workflow ID to full workflow IDs."""
    matched_ids = []

    try:
        resp = requests.get(_url(), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit(f'Could not match ID: {wf_id}. Code {resp.status_code}')
        # raise ApiError("GET /jobs".format(resp.status_code))

    workflow_list = jsonpickle.decode(resp.json()['workflow_list'])
    if workflow_list:
        for job in workflow_list:
            if job[1].startswith(wf_id):
                matched_ids.append(job[1])
        if len(matched_ids) > 1:
            logging.info(f"user-provided workflow ID {wf_id} matched multiple stored workflow IDs")
            error_exit("provided workflow ID ambiguous")
        elif not matched_ids:
            logging.info(f"user-provided workflow ID {wf_id} did not match any"
                         "stored workflow ID")
            error_exit("Provided workflow ID does not match any submitted "
                       "workflows")
        else:
            logging.info(f"user-provided workflow ID {wf_id} matched stored"
                         "workflow ID {matched_ids[0]}")
            long_wf_id = matched_ids[0]
            return long_wf_id
    else:
        print("There are currently no workflows.")


app = typer.Typer(no_args_is_help=True, add_completion=False, cls=NaturalOrderGroup)


@app.command()
def submit(wf_name: str = typer.Argument(..., help='The workflow name'),
           wf_path: pathlib.Path = typer.Argument(..., help='Path to the workflow tarball'),
           main_cwl: str = typer.Argument(..., help='filename of main CWL file'),
           yaml: str = typer.Argument(..., help='filename of YAML file'),
           workdir: pathlib.Path = typer.Argument(...,
           help='working directory for workflow containing input + output files',)):
    """Submit a new workflow."""
    if os.path.exists(wf_path):
        wf_tarball = open(wf_path, 'rb')
    else:
        error_exit(f'Workflow tarball {wf_path} cannot be found')

    # Make sure the workdir is an absolute path and exists
    workdir = os.path.expanduser(workdir)
    workdir = os.path.abspath(workdir)
    if not os.path.exists(workdir):
        error_exit(f"Workflow working directory \"{workdir}\" doesn't exist")

    # TODO: Can all of this information be sent as a file?
    data = {
        'wf_name': wf_name.encode(),
        'wf_filename': os.path.basename(wf_path).encode(),
        'main_cwl': main_cwl,
        'yaml': yaml,
        'workdir': workdir,
    }
    files = {
        'workflow_archive': wf_tarball
    }
    try:
        resp = requests.post(_url(), data=data, files=files, timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.created:  # pylint: disable=no-member
        error_exit(f"Submit for {wf_name} failed. Please check the WF Manager.")

    check_short_id_collision()
    if 'wf_id' not in resp.json():
        error_exit("wf_id not in WFM response")
    wf_id = resp.json()['wf_id']
    typer.secho("Workflow submitted! Your workflow id is "
                f"{_short_id(wf_id)}.", fg=typer.colors.GREEN)
    logging.info('Sumit workflow:  {resp.text}')
    return wf_id


@app.command()
def start(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Start a workflow with a workflow ID."""
    long_wf_id = wf_id
    try:
        resp = requests.post(_resource(long_wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        raise error_exit(f"Starting {long_wf_id} failed."
                         f" Returned {resp.status_code}")

    typer.echo(f"{resp.json()['msg']}")
    logging.info('Started  {resp.text}')


@app.command()
def package(wf_path: pathlib.Path = typer.Argument(...,
            help='Path to the workflow package directory'),
            package_dest: pathlib.Path = typer.Argument(...,
            help='Path for where the packaged workflow should be saved')
            ):
    """Package a workflow into a tarball."""
    if not os.path.isdir(wf_path):
        print(f"{wf_path} is not a valid directory.")

    # Get the filename
    wf_dir = wf_path.name
    tarball = wf_path.name + '.tgz'
    # Get the parent directory and resolve it in case the path is relative
    parent_dir = wf_path.resolve().parent
    # Just use tar with subprocess. Python's tar library is not performant.
    return_code = subprocess.run(['tar', '-C', parent_dir, '-czf', tarball, wf_dir],
                                 check=True).returncode
    package_path = package_dest.resolve()/tarball  # noqa: Not an arithmetic operation

    # Get the curent working directory
    cwd = pathlib.Path().absolute()
    if package_dest != cwd:
        # Move the tarball if the directory it's wanted in is not in the current working directory
        tarball_path = cwd/tarball  # noqa: Not an arithmetic operation
        shutil.move(tarball_path, package_path)

    if return_code != 0:
        print("Package failed")
    else:
        print(f"Package {tarball} created successfully")


@app.command()
def listall():
    """List all worklfows."""
    try:
        resp = requests.get(_url(), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager did not return workflow list')

    logging.info('List Jobs:  {resp.text}')
    workflow_list = jsonpickle.decode(resp.json()['workflow_list'])
    if workflow_list:
        typer.secho("Name\tID\tStatus", fg=typer.colors.GREEN)

        for name, wf_id, status in workflow_list:
            typer.echo(f"{name}\t{_short_id(wf_id)}\t{status}")
    else:
        typer.echo("There are currently no workflows.")

    logging.info('List workflows:  {resp.text}')


@app.command()
def query(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Get the status of a workflow."""
    # wf_id is a tuple with the short version and long version
    long_wf_id = wf_id
    try:
        resp = requests.get(_resource(long_wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('Could sucessfully query workflow manager')

    tasks_status = resp.json()['tasks_status']
    wf_status = resp.json()['wf_status']
    if tasks_status == 'Unavailable':
        typer.echo(wf_status)
    else:
        typer.echo(wf_status)
        typer.echo(tasks_status)

    logging.info('Query workflow:  {resp.text}')
    return wf_status, tasks_status


@app.command()
def pause(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Pause a workflow (Running tasks will finish)."""
    long_wf_id = wf_id
    try:
        resp = requests.patch(_resource(long_wf_id), json={'option': 'pause'},
                              timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager could not pause workflow.')
    logging.info('Pause workflow:  {resp.text}')


@app.command()
def resume(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Resume a paused workflow."""
    long_wf_id = wf_id
    try:
        resp = requests.patch(_resource(long_wf_id),
                              json={'wf_id': long_wf_id, 'option': 'resume'},
                              timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager could not resume workflow.')
    logging.info('Resume workflow:  {resp.text}')


@app.command()
def cancel(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Cancel a workflow."""
    long_wf_id = wf_id
    try:
        resp = requests.delete(_resource(long_wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.accepted:  # pylint: disable=no-member
        error_exit('WF Manager could not cancel workflow.')
    typer.secho("Workflow cancelled!", fg=typer.colors.GREEN)
    logging.info(f'Cancel workflow: {resp.text}')


@app.command()
def copy(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Copy an archived workflow."""
    long_wf_id = wf_id
    try:
        resp = requests.patch(_url(), files={'wf_id': long_wf_id}, timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager could not copy workflow.')
    archive_file = jsonpickle.decode(resp.json()['archive_file'])
    archive_filename = resp.json()['archive_filename']
    logging.info(f'Copy workflow: {resp.text}')
    return archive_file, archive_filename


@app.command()
def reexecute(wf_name: str = typer.Argument(..., help='The workflow name'),
              wf_path: pathlib.Path = typer.Argument(..., help='Path to the workflow archive')):
    """Reexecute an archived workflow."""
    if os.path.exists(wf_path):
        wf_tarball = open(wf_path, 'rb')
    else:
        error_exit(f'Workflow tarball {wf_path} cannot be found')

    data = {
        'wf_filename': os.path.basename(wf_path).encode(),
        'wf_name': wf_name.encode()
    }
    try:
        resp = requests.put(_url(), data=data,
                            files={'workflow_archive': wf_tarball}, timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.created: #noqa: member does exist
        error_exit(f"Reexecute for {wf_name} failed. Please check the WF Manager.")

    wf_id = resp.json()['wf_id']
    typer.secho("Workflow submitted! Your workflow id is "
                f"{_short_id(wf_id)}.", fg=typer.colors.GREEN)
    logging.info(f'ReExecute Workflow: {resp.text}')
    return wf_id


def main():
    """Execute bee_client."""
    global _INTERACTIVE
    _INTERACTIVE = True
    bc.init()
    app()


if __name__ == "__main__":
    app()

# Pylint is reporting no member for requests.codes even when they exist
#     ignoring them line by line
# Ignore using with for open files; used to send command.
# pylama:ignore=R1732
