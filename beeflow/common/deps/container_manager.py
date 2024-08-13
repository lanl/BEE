#!/usr/bin/env python3

"""Functions for managing the BEE depency container and associated bind mounts."""

import os
import shutil
import subprocess

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common import paths
from celery import shared_task #noqa pylama can't find celery


class NoContainerRuntime(Exception):
    """An exception for no container runtime like charliecloud or singularity."""


def check_container_runtime():
    """Check if the container runtime is currently installed."""
    # Needs to support singuarity as well
    if shutil.which("ch-convert") is None or shutil.which("ch-run") is None:
        print("ch-convert or ch-run not found. Charliecloud required"
              " for neo4j container.")
        raise NoContainerRuntime('')


def make_dep_dir():
    """Make a new bee dependency container directory."""
    bee_workdir = paths.workdir()
    bee_dir = f'{bee_workdir}/deps'
    bee_dir_exists = os.path.isdir(bee_dir)
    if not bee_dir_exists:
        os.makedirs(bee_dir)


def get_dep_dir():
    """Return the dependency directory path."""
    bee_workdir = paths.workdir()
    bee_container_dir = f'{bee_workdir}/deps/'
    return bee_container_dir


def get_container_dir(dep_name):
    """Return the depency container path."""
    container_name = dep_name + '_container'
    return get_dep_dir() + container_name


def check_container_dir(dep_name):
    """Return true if the container directory exists."""
    container_dir = get_container_dir(dep_name)
    container_dir_exists = os.path.isdir(container_dir)
    return container_dir_exists


def create_image(dep_name):
    """Create a new BEE dependency container if one does not exist.

    By default, the container is stored in /tmp/<user>/beeflow/deps.
    """
    # Can throw an exception that needs to be handled by the caller
    check_container_runtime()

    image = bc.get('DEFAULT', dep_name + '_image')

    # Check for BEE dependency container directory:
    container_dir_exists = check_container_dir(dep_name)
    if container_dir_exists:
        print(f"Already have {dep_name} container")
        return

    make_dep_dir()
    container_dir = get_container_dir(dep_name)

    # Build new dependency container
    try:
        subprocess.run(["ch-convert", "-i", "tar", "-o", "dir",
                        str(image), str(container_dir)], check=True)
    except subprocess.CalledProcessError as error:
        print(f"ch-convert failed: {error}")
        shutil.rmtree(container_dir)
        print(f"{dep_name} container mount directory {container_dir} removed")
        return

    # If neo4j, make the certificates directory
    if dep_name == 'neo4j':
        container_certs_path = os.path.join(container_dir, 'var/lib/neo4j/certificates')
        os.makedirs(container_certs_path, exist_ok=True)
