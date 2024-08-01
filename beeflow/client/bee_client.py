#!/usr/bin/env python3
"""bee-client.

This script provides an client interface to the user to manage workflows.
Capablities include submitting, starting, listing, pausing and cancelling workflows.
"""
import os
import sys
import logging
import inspect
import pathlib
import shutil
import subprocess
import tempfile
import textwrap
import time
import importlib.metadata
import jsonpickle
import requests
import typer

from beeflow.common import config_driver
from beeflow.common.cli import NaturalOrderGroup
from beeflow.common.connection import Connection
from beeflow.common import paths
from beeflow.common.parser import CwlParser
from beeflow.common.wf_data import generate_workflow_id
from beeflow.client import core
from beeflow.wf_manager.resources import wf_utils

# Length of a shortened workflow ID
short_id_len = 6 #noqa: Not a constant

# Maximum length of a workflow ID
MAX_ID_LEN = 32

# Global used to indicate whether this instance is interactive or not
_INTERACTIVE = False


logging.basicConfig(level=logging.WARNING)
WORKFLOW_MANAGER = 'bee_wfm/v1/jobs/'


class ClientError(Exception):
    """Client error class."""

    def __init__(self, *args):
        """Error constructor."""
        self.args = args


def error_exit(msg, include_caller=True):
    """Print a message and exit or raise an error with that message."""
    if include_caller:
        caller_func = str.capitalize(inspect.stack()[1].function)
        msg = caller_func + ': ' + msg
    if _INTERACTIVE:
        typer.secho(msg, fg=typer.colors.RED, file=sys.stderr)
        sys.exit(1)
    else:
        # Raise an error so that client libraries can handle it
        raise ClientError(msg) from None


def error_handler(resp):  # noqa (this is an error handler, it doesn't need to return an expression)
    """Handle a 500 error in a response."""
    if resp.status_code != 500:
        return resp
    data = resp.json()
    if 'error' not in data:
        return resp
    error = data['error']
    error_file = f'bee-error-{int(time.time())}.log'
    # Save the args and exception info to the file
    with open(error_file, 'w', encoding='utf-8') as fp:
        fp.write(f'args: {" ".join(sys.argv)}\n')
        fp.write(error)
    msg = ('An error occurred with the WFM. Please save your workflow and the '
           f'error log "{error_file}". If possible, please report this to the '
           'BEE development team.')
    msg = textwrap.fill(msg)
    error_exit(msg, include_caller=False)


def _wfm_conn():
    """Return a connection to the WFM."""
    return Connection(paths.wfm_socket(),
                      error_handler=error_handler)


def _url():
    #    """Returns URL to the workflow manager end point"""
    #    wfm_listen_port = wf_db.get_wfm_port()
    #    workflow_manager = 'bee_wfm/v1/jobs'
    #    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'
    """Return URL to the workflow manager end point."""
    return WORKFLOW_MANAGER


def _short_id(wf_id):
    return wf_id[:short_id_len]


def _resource(tag=""):
    return _url() + str(tag)


def get_wf_list():
    """Get the list of all workflows."""
    try:
        conn = _wfm_conn()
        resp = conn.get(_url(), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager did not return workflow list')

    logging.info('List Jobs:  {resp.text}')
    return jsonpickle.decode(resp.json()['workflow_list'])


def check_short_id_collision():
    """Check short workflow IDs for colliions; increase short ID length if detected."""
    global short_id_len  #noqa: Not a constant
    workflow_list = get_wf_list()
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
    workflow_list = get_wf_list()
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
        sys.exit("There are currently no workflows.")

    return None


def get_wf_status(wf_id):
    """Get workflow status."""
    try:
        conn = _wfm_conn()
        resp = conn.get(_resource(wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('Could not successfully query workflow manager')

    return resp.json()['wf_status']


app = typer.Typer(no_args_is_help=True, add_completion=False, cls=NaturalOrderGroup)
app.add_typer(core.app, name='core')
app.add_typer(config_driver.app, name='config')


@app.command()
def submit(wf_name: str = typer.Argument(..., help='the workflow name'),  # pylint:disable=R0915
           wf_path: pathlib.Path = typer.Argument(..., help='path to the workflow .tgz or dir'),
           main_cwl: str = typer.Argument(...,
           help='filename of main CWL (if using CWL tarball), '
           + 'path of main CWL (if using CWL directory)'),
           yaml: str = typer.Argument(...,
           help='filename of yaml file (if using CWL tarball), '
           + 'path of yaml file (if using CWL directory)'),
           workdir: pathlib.Path = typer.Argument(...,
           help='working directory for workflow containing input + output files',),
           no_start: bool = typer.Option(False, '--no-start', '-n',
                                         help='do not start the workflow')):
    """Submit a new workflow."""
    def is_parent(parent, path):
        """Return true if the path is a child of the other path."""
        parent = os.path.abspath(parent)
        path = os.path.abspath(path)
        return os.path.commonpath([parent]) == os.path.commonpath([parent, path])

    wf_path = wf_path.resolve()
    workdir = workdir.resolve()

    tarball_path = ""
    if os.path.exists(wf_path):
        # Check to see if the wf_path is a tarball or a directory. Package if directory
        if os.path.isdir(wf_path):
            print("Detected directory instead of packaged workflow. Packaging Directory...")
            main_cwl_path = pathlib.Path(main_cwl).resolve()
            yaml_path = pathlib.Path(yaml).resolve()

            if not main_cwl_path.exists():
                error_exit(f'Main CWL file {main_cwl} does not exist')
            if not yaml_path.exists():
                error_exit(f'YAML file {yaml} does not exist')

            # Packaging in temp dir, after copying alternate cwl_main or yaml file
            cwl_indir = is_parent(wf_path, main_cwl_path)
            yaml_indir = is_parent(wf_path, yaml_path)
            # Always create temp dir for the workflow
            tempdir_path = pathlib.Path(tempfile.mkdtemp())
            tempdir_wf_path = pathlib.Path(tempdir_path / wf_name)
            shutil.copytree(wf_path, tempdir_wf_path, dirs_exist_ok=False)
            if not cwl_indir:
                shutil.copy2(main_cwl, tempdir_wf_path)
            if not yaml_indir:
                shutil.copy2(yaml, tempdir_wf_path)
            package_path = package(tempdir_wf_path, tempdir_path)
        else:
            package_path = wf_path
        # Untar and parse workflow
        untar_path = pathlib.Path(tempfile.mkdtemp())
        untar_wf_path = unpackage(package_path, untar_path)
        main_cwl_path = untar_wf_path / pathlib.Path(main_cwl).name
        yaml_path = untar_wf_path / pathlib.Path(yaml).name
        parser = CwlParser()
        workflow_id = generate_workflow_id()
        workflow, tasks = parser.parse_workflow(workflow_id, str(main_cwl_path),
                                                job=str(yaml_path))
        tasks = [jsonpickle.encode(task) for task in tasks]

        wf_tarball = open(package_path, 'rb')
        shutil.rmtree(untar_path)
        if os.path.isdir(wf_path):
            shutil.rmtree(tempdir_path)
    else:
        error_exit(f'Workflow tarball {wf_path} cannot be found')

    # Make sure the workdir is an absolute path and exists
    workdir = os.path.expanduser(workdir)
    workdir = os.path.abspath(workdir)
    if not os.path.exists(workdir):
        error_exit(f"Workflow working directory \"{workdir}\" doesn't exist")

    # Make sure the workdir is not in /var or /var/tmp
    if os.path.commonpath([os.path.realpath('/tmp'), workdir]) == os.path.realpath('/tmp'):
        error_exit("Workflow working directory cannot be in \"/tmp\"")
    if os.path.commonpath([os.path.realpath('/var/tmp'), workdir]) == os.path.realpath('/var/tmp'):
        error_exit("Workflow working directory cannot be in \"/var/tmp\"")

    # TODO: Can all of this information be sent as a file?
    data = {
        'wf_name': wf_name.encode(),
        'wf_filename': os.path.basename(wf_path).encode(),
        'workdir': workdir,
        'workflow': jsonpickle.encode(workflow),
        'tasks': jsonpickle.encode(tasks, warn=True),
        'no_start': no_start,
    }
    files = {
        'workflow_archive': wf_tarball
    }
    try:
        conn = _wfm_conn()
        resp = conn.post(_url(), data=data, files=files, timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.created:  # pylint: disable=no-member
        if resp.status_code == 400:
            data = resp.json()
            error_exit(data['msg'])
        error_exit(f"Submit for {wf_name} failed. Please check the WF Manager.")

    check_short_id_collision()
    if 'wf_id' not in resp.json():
        error_exit("wf_id not in WFM response")
    wf_id = resp.json()['wf_id']
    typer.secho("Workflow submitted! Your workflow id is "
                f"{_short_id(wf_id)}.", fg=typer.colors.GREEN)
    logging.info('Sumit workflow:  {resp.text}')

    # Cleanup code
    if tarball_path:
        os.remove(tarball_path)

    # Store provided arguments in text file for future reference
    wf_dir = wf_utils.get_workflow_dir(wf_id)
    sub_wf_dir = wf_dir + "/submit_command_args.txt"

    f_name = open(sub_wf_dir, "w", encoding="utf-8")
    f_name.write(f"wf_name: {wf_name}\n")
    f_name.write(f"wf_path: {wf_path}\n")
    f_name.write(f"main_cwl: {main_cwl}\n")
    f_name.write(f"yaml: {yaml}\n")
    f_name.write(f"workdir: {workdir}\n")
    f_name.write(f"wf_id: {wf_id}")
    f_name.close()

    return wf_id


@app.command()
def start(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Start a workflow with a workflow ID."""
    long_wf_id = wf_id
    try:
        conn = _wfm_conn()
        resp = conn.post(_resource(long_wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code == 400:
        error_exit("Could not start workflow. It may have already been started "
                   "and ran to completion (or failure).")
    elif resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit(f"Starting {long_wf_id} failed."
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
        error_exit(f"{wf_path} is not a valid directory.")

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
        error_exit("Package failed")
    else:
        print(f"Package {tarball} created successfully")

    return package_path


@app.command()
def remove(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Remove cancelled, paused, or archived workflow with a workflow ID."""
    long_wf_id = wf_id

    wf_status = get_wf_status(wf_id)
    print(f"Workflow Status is {wf_status}")
    if wf_status in ('Cancelled', 'Paused') or 'Archived' in wf_status:
        verify = f"All stored information for workflow {_short_id(wf_id)} will be removed."
        verify += "\nContinue to remove? yes(y)/no(n): """
        response = input(verify)
        if response in ("n", "no"):
            sys.exit("Workflow not removed.")
        elif response in ("y", "yes"):
            try:
                conn = _wfm_conn()
                resp = conn.delete(_resource(long_wf_id), json={'option': 'remove'}, timeout=60)
            except requests.exceptions.ConnectionError:
                error_exit('Could not reach WF Manager.')
            if resp.status_code != requests.codes.accepted:  # pylint: disable=no-member
                error_exit('WF Manager could not remove workflow.')
            typer.secho("Workflow removed!", fg=typer.colors.GREEN)
            logging.info(f'Remove workflow: {resp.text}')
    else:
        print(f"{_short_id(wf_id)} may still be running.")
        print("The workflow must be cancelled before attempting removal.")

    sys.exit()


def unpackage(package_path, dest_path):
    """Unpackage a workflow tarball for parsing."""
    package_str = str(package_path)
    package_path = package_path.resolve()

    if not package_str.endswith('.tgz'):
        # No cleanup, maybe we should rm dest_path?
        error_exit("Invalid package name, please use the beeflow package command")
    wf_dir = pathlib.Path(package_path).stem

    return_code = subprocess.run(['tar', '-C', dest_path, '-xf', package_path],
                                 check=True).returncode
    if return_code != 0:
        # No cleanup, maybe we should rm dest_path?
        error_exit("Unpackage failed")
    else:
        print(f"Package {package_str} unpackaged successfully")
    return pathlib.Path(dest_path / wf_dir)


@app.command('list')
def list_workflows():
    """List all workflows."""
    workflow_list = get_wf_list()
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
        conn = _wfm_conn()
        resp = conn.get(_resource(long_wf_id), timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('Could not successfully query workflow manager')

    tasks_status = resp.json()['tasks_status']
    wf_status = resp.json()['wf_status']
    typer.echo(wf_status)
    for _task_id, task_name, task_state in tasks_status:
        typer.echo(f'{task_name}--{task_state}')

    logging.info('Query workflow:  {resp.text}')
    return wf_status, tasks_status


@app.command()
def metadata(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Get metadata about a given workflow."""
    try:
        conn = _wfm_conn()
        resp = conn.get(_resource(wf_id) + '/metadata', timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:  # noqa (pylama doesn't know about the okay member)
        error_exit('Could not successfully query workflow manager')

    # Print and or return the metadata
    data = resp.json()
    for key, value in data.items():
        typer.echo(f'{key} = {value}')
    return data


@app.command()
def pause(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Pause a workflow (Running tasks will finish)."""
    long_wf_id = wf_id
    try:
        conn = _wfm_conn()
        resp = conn.patch(_resource(long_wf_id), json={'option': 'pause'},
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
        conn = _wfm_conn()
        resp = conn.patch(_resource(long_wf_id),
                          json={'wf_id': long_wf_id, 'option': 'resume'},
                          timeout=60)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:  # pylint: disable=no-member
        error_exit('WF Manager could not resume workflow.')
    logging.info('Resume workflow:  {resp.text}')


@app.command()
def cancel(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Cancel a paused or running workflow."""
    long_wf_id = wf_id
    wf_status = get_wf_status(wf_id)
    if wf_status in ('Running', 'Paused'):
        try:
            conn = _wfm_conn()
            resp = conn.delete(_resource(long_wf_id), json={'option': 'cancel'}, timeout=60)

        except requests.exceptions.ConnectionError:
            error_exit('Could not reach WF Manager.')
        if resp.status_code != requests.codes.accepted:  # pylint: disable=no-member
            error_exit('WF Manager could not cancel workflow.')
        typer.secho("Workflow cancelled!", fg=typer.colors.GREEN)
        logging.info(f'Cancel workflow: {resp.text}')
    elif wf_status == "Intializing":
        print(f"Workflow is {wf_status}, try cancel later.")
    else:
        print(f"Workflow is {wf_status} cannot cancel.")


@app.command()
def copy(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """Copy an archived workflow."""
    long_wf_id = wf_id
    try:
        conn = _wfm_conn()
        resp = conn.patch(_url(), files={'wf_id': long_wf_id}, timeout=60)
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
              wf_path: pathlib.Path = typer.Argument(..., help='Path to the workflow archive'),
              workdir: pathlib.Path = typer.Argument(
                  ...,
                  help='working directory for workflow containing input + output files')
              ):
    """Reexecute an archived workflow."""
    if os.path.exists(wf_path):
        wf_tarball = open(wf_path, 'rb')
    else:
        error_exit(f'Workflow tarball {wf_path} cannot be found')

    # Make sure the workdir is an absolute path and exists
    workdir = os.path.expanduser(workdir)
    workdir = os.path.abspath(workdir)
    if not os.path.exists(workdir):
        error_exit(f"Workflow working directory \"{workdir}\" doesn't exist")

    data = {
        'wf_filename': os.path.basename(wf_path).encode(),
        'wf_name': wf_name.encode(),
        'workdir': workdir
    }
    try:
        conn = _wfm_conn()
        resp = conn.put(_url(), data=data,
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


@app.callback(invoke_without_command=True)
def version_callback(version: bool = False):
    """Beeflow."""
    # Print out the current version of the app, and then exit
    # Note above docstring gets used in the help menu
    if version:
        version = importlib.metadata.version("hpc-beeflow")
        print(version)


def main():
    """Execute bee_client."""
    global _INTERACTIVE
    _INTERACTIVE = True
    app()


if __name__ == "__main__":
    app()

# Ignore W0511: This allows us to have TODOs in the code
# Ignore R1732: Significant code restructuring required to fix
# pylama:ignore=W0511,R1732
