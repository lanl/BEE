"""Core utitilty functions."""

import os
import shutil
from pathlib import Path


def handle_rm_error(err, dir_to_check, wf_list, warn):
    """Handle IO error caused by either initializing workflows or NFS files."""
    dir_list = os.listdir(dir_to_check)
    nfs_list = [x for x in dir_list if x.startswith('.nfs')]

    if dir_list and (dir_list != nfs_list):
        print(f"Unable to remove {dir_to_check} \n {err.strerror}")

        if any('Initializing' in sublist for sublist in wf_list):
            warn('Initializing workflows may have prevented removal.\n')
            print(f"Try removing {dir_to_check} manually, to complete reset.")


def remove_bee_workdir(bee_workdir, workflow_list, warn):
    """Remove the bee_workdir directory."""
    try:
        shutil.rmtree(bee_workdir)
    except OSError as err:
        handle_rm_error(err, bee_workdir, workflow_list, warn)
    else:
        print(f"{bee_workdir} has been removed.")


def remove_dir(tmp_dir):
    """Remove temporary directory."""

    if Path(tmp_dir).exists():
        try:
            shutil.rmtree(tmp_dir)
        except OSError as err:
            print(f"Could not remove {tmp_dir}: {err}")
