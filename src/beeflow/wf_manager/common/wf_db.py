import sqlite3

from sqlite3 import Error
from collections import namedtuple


def create_connection():
    db_file = 'workflow.db'
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


def create_table(conn, stmt):
    try:
        c = conn.cursor()
        c.execute(stmt)
    except Error as e:
        print(e)


def run(stmt, params=None):
    with create_connection() as conn:
        try:
            c = conn.cursor()
            if params:
                c.execute(stmt, params)
            else:
                c.execute(stmt)
            conn.commit()
        except Error as e:
            print(e)


def get(stmt, params=None):
    with create_connection() as conn:
        try:
            c = conn.cursor()
            if params:
                c.execute(stmt, params)
            else:
                c.execute(stmt)
            result = c.fetchall()
        except Error as e:
            print(e)

        return result


def init():
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
    stmt = """INSERT INTO workflows (workflow_id, name, status)
                                    VALUES(?, ?, ?);"""
    run(stmt, [workflow_id, name, status])


def update_workflow_state(workflow_id, status):
    stmt = "UPDATE workflows SET status=? WHERE workflow_id=?"
    run(stmt, [status, workflow_id])


Workflow = namedtuple("Workflow", "id workflow_id name status")


def get_workflow(workflow_id):
    stmt = "SELECT * FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])[0]
    workflow = Workflow(*result)
    return workflow


def get_workflows():
    stmt = "SELECT * FROM workflows"
    result = get(stmt)
    workflows = [Workflow(*workflow) for workflow in result]
    return workflows


def add_task(task_id, workflow_id, name, status):
    stmt = "INSERT INTO tasks (task_id, workflow_id, name, resource, status,"\
           "slurm_id) VALUES(?, ?, ?, ?, ?, ?)"
    run(stmt, [task_id, workflow_id, name, None, status, None])


Task = namedtuple("Task", "id task_id workflow_id resource status slurm_id "
                  "name")


def get_tasks(workflow_id):
    stmt = "SELECT * FROM tasks WHERE workflow_id=?"
    result = get(stmt, [workflow_id])
    tasks = [Task(*task) for task in result]
    return tasks


def delete_workflow(workflow_id):
    stmt = "DELETE FROM workflows WHERE workflow_id=?"
    run(stmt, [workflow_id])


def update_task_state(task_id, workflow_id, status):
    stmt = "UPDATE tasks SET status=? WHERE task_id=? AND workflow_id=? "\
           "VALUES(?, ?, ?)"
    run(stmt, [status, task_id, workflow_id])


def get_task(workflow_id):
    stmt = "SELECT * FROM workflows WHERE workflow_id=?"
    result = get(stmt, [workflow_id])
    return result


def delete_task(task_id, workflow_id):
    stmt = "DELETE FROM workflows WHERE task_id=? AND workflow_id=?"
    run(stmt, [task_id, workflow_id])
