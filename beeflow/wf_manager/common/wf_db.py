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


def create_table(conn, stmt):
    """Create a new table in the database."""
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
        except Error as error:
            print(error)

        return result


def init():
    """Create the database."""
    # Create tables if they don't exist
    # Create new database
    workflows_stmt = """CREATE TABLE IF NOT EXISTS workflows (
                            id INTEGER PRIMARY KEY,
                            -- Set workflow ID to unique.
                            workflow_id INTEGER UNIQUE,
                            name TEXT,
                            status TEST NOT NULL
                                                           );"""

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
                       workflow_manager_port INTEGER,
                       task_manager_port INTEGER,
                       scheduler_port INTEGER,
                       bolt_port INTEGER
                       );"""

    conn = create_connection()
    create_table(conn, workflows_stmt)
    create_table(conn, tasks_stmt)
    create_table(conn, info_stmt)
    conn.close()


# Initialize the database
init()


def add_workflow(workflow_id, name, status):
    """Insert a new workflow into the database."""
    stmt = """INSERT INTO workflows (workflow_id, name, status)
                                    VALUES(?, ?, ?);"""
    run(stmt, [workflow_id, name, status])


def update_workflow_state(workflow_id, status):
    """Update the status in a workflow in the database."""
    stmt = "UPDATE workflows SET status=? WHERE workflow_id=?"
    run(stmt, [status, workflow_id])


Workflow = namedtuple("Workflow", "id workflow_id name status")


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
    run(stmt, [task_id, workflow_id, name, None, status, None])


Task = namedtuple("Task", "id task_id workflow_id resource status slurm_id "
                  "name")


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
    stmt = "UPDATE tasks SET status=? WHERE task_id=? AND workflow_id=? "\
           "VALUES(?, ?, ?)"
    run(stmt, [status, task_id, workflow_id])


def get_task(task_id, workflow_id):
    """Get a task associed with a workflow."""
    stmt = "SELECT * FROM workflows WHERE task_id=? AND workflow_id=?"
    result = get(stmt, [task_id, workflow_id])
    return result


def delete_task(task_id, workflow_id):
    """Delete a task associed with a workflow."""
    stmt = "DELETE FROM workflows WHERE task_id=? AND workflow_id=?"
    run(stmt, [task_id, workflow_id])
