#!/usr/bin/env python3

"""remote-client.

This script provides a client interface to the user to manage workflows remotely.
Capabilities include checking the connection to the client, getting the droppoint location,
copying files to the droppoint, and submitting the workflow to the client.
"""
import subprocess
import pathlib

import typer

from beeflow.common.config_driver import BeeConfig as bc


app = typer.Typer(no_args_is_help=True)

port = bc.get('DEFAULT', 'remote_api_port')


@app.command()
def connection(ssh_target: str = typer.Argument(..., help='the target to ssh to')):
    """Check the connection to Beeflow client via REST API."""
    result = subprocess.run(["curl", f"{ssh_target}:{port}/"], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, check=True)
    if result.returncode == 0:
        print(result.stdout)
    else:
        print(f"Error: {result.stderr}")


@app.command()
def droppoint(ssh_target: str = typer.Argument(..., help='the target to ssh to')):
    """Request drop point location on remote machine via Beeflow client REST API."""
    with open('droppoint.env', 'w', encoding='utf-8') as output_file:
        subprocess.run(["curl", f"{ssh_target}:{port}/droppoint"], stdout=output_file, check=True)


@app.command()
def copy(file_path: pathlib.Path = typer.Argument(..., help="path to copy to droppoint")):
    """Copy path to droppoint."""
    droppoint_result = subprocess.run(
        ["jq", "-r", ".droppoint", "droppoint.env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )

    droppoint_path = droppoint_result.stdout.strip()
    print(f"Copying {str(file_path)} to {droppoint_path}")

    if file_path.is_dir():
        subprocess.run(["scp", "-r", str(file_path), droppoint_path], check=True)
    else:
        subprocess.run(["scp", str(file_path), droppoint_path], check=True)


@app.command()
def submit(ssh_target: str = typer.Argument(..., help='the target to ssh to'),
           wf_name: str = typer.Argument(..., help='the workflow name'),
           tarball_name: str = typer.Argument(..., help='the tarball name'),
           main_cwl_file: str = typer.Argument(..., help='filename of main CWL'),
           job_file: str = typer.Argument(..., help='filename of yaml file')):
    """Submit the workflow to Beeflow client."""
    subprocess.run(["curl", f"{ssh_target}:{port}/submit_long/{wf_name}/{tarball_name}/{main_cwl_file}/{job_file}"], check=True)
