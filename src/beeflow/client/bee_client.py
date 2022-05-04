#!/usr/bin/env python3
import os
import logging
import typer
import click
import requests
from pathlib import Path
import jsonpickle
import inspect
from beeflow.common.config_driver import BeeConfig


# Length of a shortened workflow ID
short_id_len = 6

# Maximum length of a workflow ID
MAX_ID_LEN = 32


logging.basicConfig(level=logging.WARNING)
workflow_manager = 'bee_wfm/v1/jobs'


def error_exit(msg):
    caller_func = str.capitalize(inspect.stack()[1].function)
    msg = caller_func + ': ' + msg
    typer.secho(msg, fg=typer.colors.RED)
    exit(1)


def _url():
    """Returns URL to the workflow manager end point"""
    WM_PORT = 5000
    if bc.userconfig.has_section('workflow_manager'):
        wfm_listen_port = bc.userconfig['workflow_manager'].get('listen_port',
                                                                WM_PORT)
    else:
        print("[workflow_manager] section not found in configuration file."
              "Default port WM_PORT will be used.")
        wfm_listen_port = WM_PORT
    return f'http://127.0.0.1:{wfm_listen_port}/{workflow_manager}/'


bc = BeeConfig()


def _short_id(wf_id):
    return wf_id[:short_id_len]


def _resource(tag=""):
    return _url() + str(tag)


class NaturalOrderGroup(click.Group):
    def list_commands(self, ctx):
        return self.commands.keys()


# Check short workflow IDs for colliions, increase short ID
# length if any detected
def check_short_id_collision():
    global short_id_len
    resp = requests.get(_url())
    if resp.status_code != requests.codes.okay:
        error_exit("Checking for ID collision failed: {resp.status_code}")

    job_list = jsonpickle.decode(resp.json()['job_list'])
    if job_list:
        while short_id_len < MAX_ID_LEN:
            id_list = [_short_id(job[1]) for job in job_list]
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


# Match user-provided short workflow ID to full workflow IDs
def match_short_id(wf_id):
    matched_ids = []

    try:
        resp = requests.get(_url())
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:
        error_exit(f'Could not match ID: {wf_id}. Code {resp.status_code}')
        # raise ApiError("GET /jobs".format(resp.status_code))

    job_list = jsonpickle.decode(resp.json()['job_list'])
    if job_list:
        for job in job_list:
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
           wf_path: Path = typer.Argument(..., help='Path to the workflow tarball'),
           main_cwl: str = typer.Argument(..., help='filename of main CWL file'),
           yaml: str = typer.Argument(..., help='filename of YAML file'),
           ):
    """
    Submit a new workflow
    """
    if os.path.exists(wf_path):
        wf_tarball = open(wf_path, 'rb')
    else:
        error_exit(f'Workflow tarball {wf_path} cannot be found')

    files = {
        'wf_name': wf_name.encode(),
        'wf_filename': os.path.basename(wf_path).encode(),
        'workflow': wf_tarball,
        'main_cwl': main_cwl,
        'yaml': yaml
    }

    try:
        resp = requests.post(_url(), files=files)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.created:
        error_exit(f"Submit for {wf_name} failed. Please check the WF Manager.")

    check_short_id_collision()
    wf_id = resp.json()['wf_id']
    typer.secho("Workflow submitted! Your workflow id is "
                f"{_short_id(wf_id)}.", fg=typer.colors.GREEN)


@app.command()
def start(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Start a workflow with a workflow ID
    """
    long_wf_id = wf_id
    try:
        resp = requests.post(_resource(long_wf_id))
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:
        raise error_exit(f"Starting {long_wf_id} failed."
                         f" Returned {resp.status_code}")

    typer.echo("Started job!")


@app.command()
def list():
    """
    List all worklfows
    """
    try:
        resp = requests.get(_url())
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:
        print(f"Returned {resp.status_code}")
        # raise ApiError("GET /jobs".format(resp.status_code))

    logging.info("List Jobs: " + resp.text)
    job_list = jsonpickle.decode(resp.json()['job_list'])
    if job_list:
        typer.secho("Name\tID\tStatus", fg=typer.colors.GREEN)

        for name, wf_id, status in job_list:
            typer.echo(f"{name}\t{_short_id(wf_id)}\t{status}")
    else:
        typer.echo("There are currently no workflows.")


@app.command()
def query(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Get the status of a workflow
    """
    # wf_id is a tuple with the short version and long version
    long_wf_id = wf_id
    try:
        resp = requests.get(_resource(long_wf_id))
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:
        # raise ApiError("Query failed".format(resp.status_code, matched_id))
        pass
    tasks_status = resp.json()['tasks_status']
    wf_status = resp.json()['wf_status']
    if tasks_status == 'Unavailable':
        typer.echo(wf_status)
    else:
        typer.echo(wf_status)
        typer.echo(tasks_status)


@app.command()
def pause(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Pause a workflow (Running jobs will finish)
    """
    long_wf_id = wf_id
    try:
        resp = requests.patch(_resource(long_wf_id), json={'option': 'pause'})
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:
        # raise ApiError("PAUSE /jobs{}".format(resp.status_code, matched_id))
        pass
    logging.info('Pause job: ' + resp.text)


@app.command()
def resume(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Resume a paused workflow
    """
    long_wf_id = wf_id
    try:
        resp = requests.patch(_resource(long_wf_id),
                              json={'wf_id': long_wf_id, 'option': 'resume'})
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    if resp.status_code != requests.codes.okay:
        # raise ApiError("RESUME /jobs{}".format(resp.status_code, matched_id))
        pass
    logging.info('Resume job: ' + resp.text)


@app.command()
def cancel(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Cancel a workflow
    """
    long_wf_id = wf_id
    try:
        resp = requests.delete(_resource(long_wf_id))
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')
    # Returns okay if the resource has been deleted
    # Non-blocking so it returns accepted
    if resp.status_code != requests.codes.accepted:
        # raise ApiError("DELETE /jobs{}".format(resp.status_code, matched_id))
        pass
    typer.secho("Workflow cancelled!", fg=typer.colors.GREEN)


@app.command()
def copy(wf_id: str = typer.Argument(..., callback=match_short_id)):
    """
    Copy an archived workflow
    """
    long_wf_id = wf_id
    try:
        resp = requests.patch(_url(), files={'wf_id': long_wf_id})
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.okay:
        # raise ApiError("COPY /jobs{}".format(resp.status_code, matched_id))
        pass
    archive_file = jsonpickle.decode(resp.json()['archive_file'])
    archive_filename = resp.json()['archive_filename']
    return archive_file, archive_filename


@app.command()
def reexecute(wf_name: str = typer.Argument(...),
              archive_path: Path = typer.Argument(...)):
    """
    Reexecute an archived workflow
    """
    files = {
        'filename': os.path.basename(archive_path).encode(),
        'workflow_archive': open(archive_path, 'rb'),
        'wf_name': wf_name.encode()
    }
    try:
        resp = requests.put(_url(), files=files)
    except requests.exceptions.ConnectionError:
        error_exit('Could not reach WF Manager.')

    if resp.status_code != requests.codes.created:
        raise error_exit("REEXECUTE /jobs{}".format(resp.status_code))

    logging.info("ReExecute Workflow: " + resp.text)

    wf_id = resp.json()['wf_id']
    return wf_id


def main():
    app()


if __name__ == "__main__":
    app()
