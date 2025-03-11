"""Utility functions for client interface."""


import os
import sys
import subprocess
import getpass
import typer

from beeflow.common import config_driver
from beeflow.common.db import client_db
from beeflow.common.db import bdb

def warn(*pargs):
    """Print a red warning message."""
    typer.secho(' '.join(pargs), fg=typer.colors.RED, file=sys.stderr)


def db_path():
    """Return the client database path."""
    bee_workdir = config_driver.BeeConfig.get('DEFAULT', 'bee_workdir')
    return os.path.join(bee_workdir, 'client.db')


def set_backend_status(new_status):
    """Set backend flag to true in database."""
    db = bdb.connect_db(client_db, db_path())
    db.info.set_backend_status(new_status)

def check_backend_status():
    """Check if backend flag has been set."""
    db = bdb.connect_db(client_db, db_path())
    status = db.info.get_backend_status()
    return status

def reset_client_db():
    """Reset client db when beeflow is stopped."""
    setup_hostname("")
    set_backend_status("")


def get_hostname():
    """Check if beeflow is running somewhere else."""
    db = bdb.connect_db(client_db, db_path())
    curr_hn = db.info.get_hostname()
    return curr_hn


def setup_hostname(start_hn):
    """Set up front end name when beeflow core start is returned."""
    db = bdb.connect_db(client_db, db_path())


def check_backend_jobs(start_hn, command=False):
    """Check if there is an instance of beeflow running on a backend node."""
    user_name = getpass.getuser()
    cmd = ['squeue', '-u', f'{user_name}', '-o', '%N', '-h']
    resp = subprocess.run(cmd, text=True, check=True, stdout=subprocess.PIPE)

    # iterate through available nodes
    data = resp.stdout.splitlines()
    cur_alloc = False
    if get_hostname() in data:
        cur_alloc = True

    if cur_alloc:
        if command:
            warn(f'beeflow was started on "{get_hostname()}" and you are trying to '
                 f'run a command on "{start_hn}".')
            sys.exit(1)
        else:
            warn(f'beeflow was started on compute node "{get_hostname()}" '
                 'and it is still running. ')
            sys.exit(1)
    else:  # beeflow was started on compute node but user no longer owns node
        if command:
            warn('beeflow was started on a compute node (no longer owned by user)')
            sys.exit(1)
        else:
            warn('beeflow was started on a compute node (no longer owned by user) and '
                 'not stopped correctly. ')
            warn("Resetting client database.")
            reset_client_db()
            setup_hostname(start_hn)  # add to client db

def check_db_flags(start_hn):
    """Check that beeflow was stopped correctly during the last run."""
    if get_hostname() and get_hostname() != start_hn and check_backend_status() == "":
        warn(f'Error: beeflow is already running on "{get_hostname()}".')
        sys.exit(1)
    if get_hostname() and get_hostname() != start_hn and check_backend_status() == "true":
        check_backend_jobs(start_hn)

def check_hostname(curr_hn):
    """Check current front end name matches the one beeflow was started on."""
    print(f'get_hostname() gives {get_hostname()}')
    if get_hostname() and curr_hn != get_hostname() and check_backend_status() == "":
        warn(f'beeflow was started on "{get_hostname()}" and you are trying to '
             f'run a command on "{curr_hn}".')
        sys.exit(1)
    elif get_hostname() and curr_hn != get_hostname() and check_backend_status() == "true":
        check_backend_jobs(curr_hn, command=True)
    if get_hostname() == "" and check_backend_status() == "":
        warn('beeflow has not been started!')
        sys.exit(1)





