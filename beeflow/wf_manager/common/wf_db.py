"""Contains functions for managing a database for workflow and task information."""

import sqlite3
from sqlite3 import Error
from collections import namedtuple
import os
from beeflow.common.config_driver import BeeConfig as bc


def create_connection():
    """Create a new connection with the workflow database."""
    db_file = os.path.join(bc.get('DEFAULT', 'bee_workdir'), 'workflow.db')
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as error:
        print(error)
    return conn


def create_table(stmt):
    """Create a new table in the database."""
    with create_connection() as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(stmt)
        except Error as error:
            print(error)


def run(stmt, params=None):
    """Run the sql statement on the database. Doesn't return anything."""
    with create_connection() as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(stmt, params)
            else:
                cursor.execute(stmt)
            conn.commit()
        except Error as error:
            print(error)


def get(stmt, params=None):
    """Run the sql statement on the database and return the result."""
    with create_connection() as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(stmt, params)
            else:
                cursor.execute(stmt)
            result = cursor.fetchall()
        except Error:
            result = None
        return result


def table_exists(table_name):
    """Return true if a table exists and false if not."""
    stmt = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    result = get(stmt)
    return len(result) != 0


def get_table_length(table):
    """Return the number of rows in a table."""
    stmt = f"SELECT COUNT(*) from {table}"
    result = get(stmt)
    rows = result[0][0]
    return rows


def init_info():
    """Insert a new workflow into the database."""
    stmt = """INSERT INTO info (wfm_port, tm_port, sched_port, num_workflows)
                                    VALUES(?, ?, ?, ?);"""
    run(stmt, [-1, -1, -1, 0])


def init_tables():
    """Create the database."""
    # Create tables if they don't exist
    # Create new database
    workflows_stmt = """CREATE TABLE IF NOT EXISTS workflows (
                            id INTEGER PRIMARY KEY,
                            -- Set workflow ID to unique.
                            workflow_id INTEGER UNIQUE,
                            name TEXT,
                            status TEST NOT NULL,
                            run_dir STR,
                            bolt_port INTEGER,
                            gdb_pid INTEGER,
                            init_task_id INTEGER);"""

    tasks_stmt = """CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    task_id INTEGER UNIQUE,
                    workflow_id INTEGER NOT NULL,
                    name TEXT,
                    resource TEXT,
                    status TEXT,
                    slurm_id INTEGER,
                    FOREIGN KEY (workflow_id)
                        REFERENCES workflows (workflow_id)
                            ON DELETE CASCADE
                            ON UPDATE NO ACTION);"""

    info_stmt = """CREATE TABLE IF NOT EXISTS info (
                       id INTEGER PRIMARY KEY,
                       wfm_port INTEGER,
                       tm_port INTEGER,
                       sched_port INTEGER,
                       num_workflows INTEGER
                       );"""

    if not table_exists('workflows'):
        create_table(workflows_stmt)
    if not table_exists('tasks'):
        create_table(tasks_stmt)
    if not table_exists('info'):
        create_table(info_stmt)
        init_info()


Info = namedtuple("Info", "id wfm_port tm_port sched_port num_workflows")


def get_info():
    """Return an info object containing port information."""
    stmt = "SELECT * FROM info"
    result = get(stmt)
    info = Info(*result[0])
    return info


def get_wfm_port():
    """Return workflow manager port."""
    stmt = "SELECT wfm_port FROM info"
    result = get(stmt)
    wfm_port = result[0][0]
    return wfm_port


def get_tm_port():
    """Return task manager port."""
    stmt = "SELECT tm_port FROM info"
    result = get(stmt)
    tm_port = result[0][0]
    return tm_port


def get_sched_port():
    """Return scheduler port."""
    stmt = "SELECT sched_port FROM info"
    result = get(stmt)
    sched_port = result[0][0]
    return sched_port


def get_num_workflows():
    """Return scheduler port."""
    stmt = "SELECT num_workflows FROM info"
    result = get(stmt)
    sched_port = result[0][0]
    return sched_port


def increment_num_workflows():
    """Set workflow manager port."""
    stmt = "UPDATE info SET num_workflows = num_workflows + 1"
    run(stmt)


def set_wfm_port(new_port):
    """Set workflow manager port."""
    if not table_exists('info'):
        # Initialize the database
        init_tables()

    stmt = "UPDATE info SET wfm_port=?"
    run(stmt, [new_port])


def set_tm_port(new_port):
    """Set workflow manager port."""
    if not table_exists('info'):
        # Initialize the database
        init_tables()
    stmt = "UPDATE info SET tm_port=?"
    run(stmt, [new_port])


def set_sched_port(new_port):
    """Set workflow manager port."""
    if not table_exists('info'):
        # Initialize the database
        init_tables()
    stmt = "UPDATE info SET sched_port=?"
    run(stmt, [new_port])


def add_workflow(workflow_id, name, status, run_dir, bolt_port, gdb_pid):
    """Insert a new workflow into the database."""
    if not table_exists('workflows'):
        # Initialize the database
        init_tables()

    stmt = ("INSERT INTO workflows (workflow_id, name, status, run_dir, bolt_port, gdb_pid) "
            "VALUES(?, ?, ?, ?, ?, ?);"
            )
    run(stmt, [workflow_id, name, status, run_dir, bolt_port, gdb_pid])


def complete_gdb_init(workflow_id, gdb_pid):
    """Complete the GDB init process for a workflow."""
    stmt = "UPDATE workflows SET gdb_pid=?, status=? WHERE workflow_id = ?"
    run(stmt, [gdb_pid, 'Pending', workflow_id])


def init_workflow(workflow_id, name, run_dir, bolt_port, http_port, https_port, init_task_id):
    """Insert a new workflow into the database."""
    if not table_exists('workflows'):
        # Initialize the database
        init_tables()

    stmt = """INSERT INTO workflows (workflow_id, name, status, run_dir, bolt_port,
                                     http_port, https_port, gdb_pid, init_task_id)
              VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);"""
    run(stmt, [workflow_id, name, 'Initializing', run_dir, bolt_port, http_port,
               https_port, -1, init_task_id])


def update_workflow_state(workflow_id, status):
    """Update the status in a workflow in the database."""
    stmt = "UPDATE workflows SET status=? WHERE workflow_id=?"
    run(stmt, [status, workflow_id])


Workflow = namedtuple("Workflow", "id workflow_id name status run_dir bolt_port gdb_pid")


def get_workflow_state(workflow_id):
    """Return the bolt port associated with a workflow."""
    stmt = "SELECT state FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    state = result[0]
    return state


def get_bolt_port(workflow_id):
    """Return the bolt port associated with a workflow."""
    stmt = "SELECT bolt_port FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])
    result = get(stmt, [workflow_id])[0]
    bolt_port = result[0]
    return bolt_port


def get_gdb_pid(workflow_id):
    """Return the bolt port associated with a workflow."""
    stmt = "SELECT gdb_pid FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    gdb_pid = result[0]
    return gdb_pid


def get_init_task_id(workflow_id):
    """Return the task ID for the GDB initialization."""
    stmt = "SELECT init_task_id FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    return result[0]


def get_run_dir(workflow_id):
    """Return the bolt port associated with a workflow."""
    stmt = "SELECT run_dir FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    run_dir = result[0]
    return run_dir


def get_workflow(workflow_id):
    """Return a workflow object."""
    stmt = "SELECT * FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    workflow = Workflow(*result)
    return workflow


def get_workflows():
    """Return a list of all the workflows."""
    stmt = "SELECT * FROM workflows"
    result = get(stmt)
    workflows = [Workflow(*workflow) for workflow in result]
    return workflows


def add_task(task_id, workflow_id, name, status):
    """Add a task to the database associated with the workflow id specified."""
    stmt = "INSERT INTO tasks (task_id, workflow_id, name, resource, status,"\
           "slurm_id) VALUES(?, ?, ?, ?, ?, ?)"
    run(stmt, [task_id, workflow_id, name, "", status, -1])


Task = namedtuple("Task", "id task_id workflow_id name resource status"
                  " slurm_id")


def get_tasks(workflow_id):
    """Get all tasks associated with a particular workflow."""
    stmt = "SELECT * FROM tasks WHERE workflow_id=?"
    result = get(stmt, [workflow_id])
    tasks = [Task(*task) for task in result]
    return tasks


def delete_workflow(workflow_id):
    """Delete a workflow from the database."""
    stmt = "DELETE FROM workflows WHERE workflow_id=?"
    run(stmt, [workflow_id])


def update_task_state(task_id, workflow_id, status):
    """Update the state of a task."""
    stmt = "UPDATE tasks SET status=? WHERE task_id=? AND workflow_id=? "
    run(stmt, [status, task_id, workflow_id])


def get_task(task_id, workflow_id):
    """Get a task associed with a workflow."""
    stmt = "SELECT * FROM task WHERE task_id=? AND workflow_id=?"
    result = get(stmt, [task_id, workflow_id])
    return result


def delete_task(task_id, workflow_id):
    """Delete a task associed with a workflow."""
    stmt = "DELETE FROM tasks WHERE task_id=? AND workflow_id=?"
    run(stmt, [task_id, workflow_id])
