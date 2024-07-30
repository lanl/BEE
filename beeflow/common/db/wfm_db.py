"""Workflow Manager database code."""

from collections import namedtuple

from beeflow.common.db import bdb


class WorkflowInfo:
    """Workflow Info object."""

    def __init__(self, db_file):
        """Initialize Info and db file."""
        self.Info = namedtuple("Info", "id wfm_port tm_port sched_port num_workflows bolt_port http_port https_port gdb_pid") # noqa Snake Case
        self.db_file = db_file

    def set_port(self, component, new_port):
        """Set port for the specified component."""
        stmt = f"UPDATE info set {component}_port=?"
        bdb.run(self.db_file, stmt, [new_port])

    def get_port(self, component):
        """Return port for the specified component."""
        # Need to add code here to make sure we chose a valid component.
        stmt = f"SELECT {component}_port FROM info"
        result = bdb.getone(self.db_file, stmt)[0]
        port = result
        return port

    def increment_num_workflows(self):
        """Set workflow manager port."""
        stmt = "UPDATE info SET num_workflows = num_workflows + 1"
        bdb.run(self.db_file, stmt)

    def get_num_workflows(self):
        """Return scheduler port."""
        stmt = "SELECT num_workflows FROM info"
        result = bdb.getone(self.db_file, stmt)
        sched_port = result[0][0]
        return sched_port

    def get_info(self):
        """Return an info object containing port information."""
        stmt = "SELECT * FROM info"
        result = bdb.getone(self.db_file, stmt)
        info = self.Info(*result)
        return info

    def get_gdb_pid(self):
        """Return the gdb pid."""
        stmt = "SELECT gdb_pid FROM info"
        result = bdb.getone(self.db_file, stmt)[0]
        gdb_pid = result
        return gdb_pid

    def update_gdb_pid(self, gdb_pid):
        """Update the gdb PID."""
        stmt = "UPDATE info SET gdb_pid=?"
        bdb.run(self.db_file, stmt, [gdb_pid])


class Workflows:
    """Workflow database object."""

    def __init__(self, db_file):
        """Initialize Task, db_file, and Workflow object."""
        self.Task = namedtuple("Task", "id task_id workflow_id name resource state slurm_id") #noqa
        self.db_file = db_file
        self.Workflow = namedtuple("Workflow", "id workflow_id name state run_dir") #noqa

    def get_workflow(self, workflow_id):
        """Return a workflow object."""
        stmt = "SELECT * FROM workflows WHERE workflow_id=?"
        result = bdb.getone(self.db_file, stmt, [workflow_id])
        workflow = self.Workflow(*result)
        return workflow

    def get_workflows(self):
        """Return a list of all the workflows."""
        stmt = "SELECT * FROM workflows"
        result = bdb.getall(self.db_file, stmt)
        workflows = [self.Workflow(*workflow) for workflow in result]
        return workflows

    def init_workflow(self, workflow_id, name, run_dir):
        """Insert a new workflow into the database."""
        stmt = """INSERT INTO workflows (workflow_id, name, state, run_dir)
                  VALUES(?, ?, ?, ?);"""
        bdb.run(self.db_file, stmt, [workflow_id, name, 'Initializing', run_dir])

    def delete_workflow(self, workflow_id):
        """Delete a workflow from the database."""
        stmt = "DELETE FROM workflows WHERE workflow_id=?"
        bdb.run(self.db_file, stmt, [workflow_id])

    def update_workflow_state(self, workflow_id, state):
        """Update the state in a workflow in the database."""
        stmt = "UPDATE workflows SET state=? WHERE workflow_id=?"
        bdb.run(self.db_file, stmt, [state, workflow_id])

    def get_workflow_state(self, workflow_id):
        """Return the bolt port associated with a workflow."""
        stmt = "SELECT state FROM workflows WHERE workflow_id=?"
        result = bdb.getone(self.db_file, stmt, [workflow_id])[0]
        state = result
        return state

    def add_task(self, task_id, workflow_id, name, state):
        """Add a task to the database associated with the workflow id specified."""
        stmt = "INSERT INTO tasks (task_id, workflow_id, name, resource, state,"\
               "slurm_id) VALUES(?, ?, ?, ?, ?, ?)"
        bdb.run(self.db_file, stmt, [task_id, workflow_id, name, "", state, -1])

    def delete_task(self, task_id, workflow_id):
        """Delete a task associed with a workflow."""
        stmt = "DELETE FROM tasks WHERE task_id=? AND workflow_id=?"
        bdb.run(self.db_file, stmt, [task_id, workflow_id])

    def update_task_state(self, task_id, workflow_id, state):
        """Update the state of a task."""
        stmt = "UPDATE tasks SET state=? WHERE task_id=? AND workflow_id=?"
        bdb.run(self.db_file, stmt, [state, task_id, workflow_id])

    def get_tasks(self, workflow_id):
        """Get all tasks associated with a particular workflow."""
        stmt = "SELECT * FROM tasks WHERE workflow_id=?"
        result = bdb.getall(self.db_file, stmt, [workflow_id])
        tasks = [self.Task(*task) for task in result]
        return tasks

    def get_task(self, task_id, workflow_id):
        """Get a task associed with a workflow."""
        stmt = "SELECT * FROM tasks WHERE task_id=? AND workflow_id=?"
        result = bdb.getone(self.db_file, stmt, [task_id, workflow_id])
        return result

    def get_run_dir(self, workflow_id):
        """Return the run directory."""
        stmt = "SELECT run_dir FROM info WHERE workflow_id=?"
        result = bdb.getone(self.db_file, stmt, [workflow_id])[0]
        run_dir = result
        return run_dir


class WorkflowDB:
    """Workflow manager database."""

    def __init__(self, db_file):
        """Initialize tables and db file."""
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        """Initialize the tables."""
        workflows_stmt = """CREATE TABLE IF NOT EXISTS workflows (
                                id INTEGER PRIMARY KEY,
                                -- Set workflow ID to unique.
                                workflow_id INTEGER UNIQUE,
                                name TEXT,
                                state TEST NOT NULL,
                                run_dir STR
                                );"""

        tasks_stmt = """CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        task_id INTEGER,
                        workflow_id INTEGER NOT NULL,
                        name TEXT,
                        resource TEXT,
                        state TEXT,
                        slurm_id INTEGER,
                        UNIQUE(task_id, workflow_id) ON CONFLICT ABORT,
                        FOREIGN KEY (workflow_id)
                            REFERENCES workflows (workflow_id)
                                ON DELETE CASCADE
                                ON UPDATE NO ACTION);"""

        info_stmt = """CREATE TABLE IF NOT EXISTS info (
                           id INTEGER PRIMARY KEY,
                           wfm_port INTEGER,
                           tm_port INTEGER,
                           sched_port INTEGER,
                           num_workflows INTEGER,
                           bolt_port INTEGER,
                           http_port INTEGER,
                           https_port INTEGER,
                           gdb_pid INTEGER
                           );"""

        bdb.create_table(self.db_file, workflows_stmt)
        bdb.create_table(self.db_file, tasks_stmt)
        if not bdb.table_exists(self.db_file, 'info'):
            bdb.create_table(self.db_file, info_stmt)
            # insert a new workflow into the database
            stmt = """INSERT INTO info (wfm_port, tm_port, sched_port, num_workflows,
                bolt_port, http_port, https_port, gdb_pid) VALUES(?, ?, ?, ?, ?, ?, ?, ?);"""
            bdb.run(self.db_file, stmt, [-1, -1, -1, 0, -1, -1, -1, -1])

    @property
    def workflows(self):
        """Get workflow info from the database."""
        return Workflows(self.db_file)

    @property
    def info(self):
        """Get workflow info from the database."""
        return WorkflowInfo(self.db_file)


def open_db(db_file):
    """Open a new database."""
    return WorkflowDB(db_file)
