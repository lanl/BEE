#!/usr/bin/env python3

"""remote-client.

This script provides a client interface to the user to manage workflows remotely.
Capabilities include checking the connection to the client, getting the droppoint location,
copying files to the droppoint, and submitting the workflow to the client.
"""
import subprocess
import pathlib
import sys
import json

import typer

from beeflow.common.config_driver import BeeConfig as bc


def warn(*pargs):
    """Print a red warning message."""
    typer.secho(' '.join(pargs), fg=typer.colors.RED, file=sys.stderr)


def remote_port_val():
    """Return the value of the remote port."""
    return bc.get('DEFAULT', 'remote_api_port')


app = typer.Typer(no_args_is_help=True)


@app.command()
def connection(ssh_target: str = typer.Argument(..., help='the target to ssh to')):
    """Check the connection to Beeflow client via REST API."""
    port = remote_port_val()
    try:
        result = subprocess.run(
            ["curl", f"{ssh_target}:{port}/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError:
        warn(f'Connection to {ssh_target}:{port} failed.')

        # check if the remote API was started
        check_command = 'ssh {ssh_target} "ps aux | grep $USER | grep \'gunicorn\'"'
        result = subprocess.run(
                check_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
        )
        lines = result.stdout.strip().splitlines()
        if not any("beeflow.remote.remote:create_app" in element for element in lines):
            warn(f'Remote API has not been started on {ssh_target}. '
                  'Use remote flag when starting beeflow.')
        sys.exit(1)


@app.command()
def droppoint(ssh_target: str = typer.Argument(..., help='the target to ssh to')):
    """Request drop point location on remote machine via Beeflow client REST API."""
    port = remote_port_val()
    try:
        result = subprocess.run(
            ["curl", f"{ssh_target}:{port}/droppoint"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        with open('droppoint.env', 'w', encoding='utf-8') as output_file:
            output_file.write(result.stdout)
        print("Droppoint information saved to droppoint.env")

    except subprocess.CalledProcessError:
        warn(f'Failed to retrieve droppoint from {ssh_target}:{port}.'
             ' Check connection to beeflow.')
        sys.exit(1)


@app.command()
def copy(user: str = typer.Argument(..., help='the username on the remote system'),
         ssh_target: str = typer.Argument(..., help="the target to ssh to"),
         file_path: pathlib.Path = typer.Argument(..., help="path to copy to droppoint")):
    """Copy path to droppoint."""
    if not file_path.exists():
        warn(f'Error: File or directory {file_path} does not exist.')
        sys.exit(1)

    try:
        with open("droppoint.env", "r", encoding="utf-8") as f:
            config = json.load(f)
        droppoint_path = config.get("droppoint", "")

        if not droppoint_path:
            warn('Error: Could not retrieve droppoint location.')
            sys.exit(1)

        print(f"Copying {str(file_path)} to {droppoint_path}")

        subprocess.run(["rsync", "-a", str(file_path), f"{user}@{ssh_target}:{droppoint_path}"],
                        check=True)

        print("Copy successful.")
    except FileNotFoundError:
        warn("Error: File droppoint.env not found. Did you run"
             " 'beeflow remote droppoint $ssh_target' to create this file?")
        sys.exit(1)
    except json.JSONDecodeError as jde:
        warn(f'Error reading JSON configuration: {jde}')
        sys.exit(1)
    except subprocess.CalledProcessError as err:
        warn(f'Error copying file: {err.stderr}')
        sys.exit(1)


@app.command()
def submit(ssh_target: str = typer.Argument(..., help='the target to ssh to'),
           wf_name: str = typer.Argument(..., help='the workflow name'),
           tarball_name: str = typer.Argument(..., help='the tarball name'),
           main_cwl: str = typer.Argument(..., help='filename of main CWL'),
           job_file: str = typer.Argument(..., help='filename of yaml file')):
    """Submit the workflow to Beeflow client."""
    port = remote_port_val()
    try:
        result = subprocess.run(
            [
                "curl",
                f"{ssh_target}:{port}/submit_long/{wf_name}/{tarball_name}/{main_cwl}/{job_file}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        response = result.stdout.strip()

        try:
            response_json = json.loads(response)
        except json.JSONDecodeError:
            warn(f'Unexpected response from API: {response}')
            sys.exit(1)

        # Check if API response contains an error
        if "error" in response_json:
            warn(f"Error submitting workflow: {response_json['error']}")
            sys.exit(1)

        print(response_json.get('result'))

    except subprocess.CalledProcessError as err:
        warn(f'Failed to submit workflow. Error: {err.stderr}')
        sys.exit(1)


@app.command("core-status")
def core_status(ssh_target: str = typer.Argument(..., help='the target to ssh to')):
    """Check the status of BEEflow and the components."""
    port = remote_port_val()
    try:
        result = subprocess.run(
            ["curl", f"{ssh_target}:{port}/core/status/"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError:
        warn(f'Failed to check status on {ssh_target}:{port}. Check connection to beeflow.')
        sys.exit(1)
