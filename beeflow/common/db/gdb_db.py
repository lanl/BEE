"""Graph Database SQL implementation."""

import json
from beeflow.common.db import bdb
from beeflow.common.object_models import (Workflow, Task, Requirement, Hint, 
InputParameter, OutputParameter, StepInput, StepOutput)

class SQL_GDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        wfs_stmt = """CREATE TABLE IF NOT EXISTS workflow (
            id TEXT PRIMARY KEY,
            name TEXT,
            state TEXT,
            workdir TEXT,
            main_cwl TEXT,
            wf_path TEXT,
            yaml TEXT,
            reqs JSON,
            hints JSON,
            restart INTEGER DEFAULT 0
        );"""
        
        wf_inputs_stmt = """CREATE TABLE IF NOT EXISTS workflow_input (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            type TEXT,
            value TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE
        );"""

        wf_outputs_stmt = """CREATE TABLE IF NOT EXISTS workflow_output (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            type TEXT,
            value TEXT,
            source TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE
        );"""

        tasks_stmt = """CREATE TABLE IF NOT EXISTS task (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            name TEXT,
            state TEXT,
            workdir TEXT,
            base_command TEXT,
            stdout TEXT,
            stderr TEXT,
            reqs JSON,
            hints JSON,
            metadata JSON,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE
        );"""

        task_inputs_stmt = """CREATE TABLE IF NOT EXISTS task_input (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            type TEXT,
            value TEXT,
            default_val TEXT,
            source TEXT,
            prefix TEXT,
            position INTEGER,
            value_from TEXT,
            FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE
        );"""

        task_outputs_stmt = """CREATE TABLE IF NOT EXISTS task_output (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            type TEXT,
            value TEXT,
            glob TEXT,
            FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE
        );"""

        # FROM task depends on TO task
        task_deps_stmt = """CREATE TABLE IF NOT EXISTS task_dep (
                depending_task_id TEXT NOT NULL,
                depends_on_task_id   TEXT NOT NULL,
                PRIMARY KEY (depending_task_id, depends_on_task_id),
                FOREIGN KEY (depending_task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (depends_on_task_id)   REFERENCES task(id) ON DELETE CASCADE
        );"""

        # FROM task restarted from TO task
        task_rst_stmt = """CREATE TABLE IF NOT EXISTS task_restart (
                restarting_task_id TEXT NOT NULL,
                restarted_from_task_id   TEXT NOT NULL,
                PRIMARY KEY (restarting_task_id, restarted_from_task_id),
                FOREIGN KEY (restarting_task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (restarted_from_task_id)   REFERENCES task(id) ON DELETE CASCADE
        );"""

        bdb.create_table(self.db_file, wfs_stmt)
        bdb.create_table(self.db_file, wf_inputs_stmt)
        bdb.create_table(self.db_file, wf_outputs_stmt)
        bdb.create_table(self.db_file, tasks_stmt)
        bdb.create_table(self.db_file, task_inputs_stmt)
        bdb.create_table(self.db_file, task_outputs_stmt)
        bdb.create_table(self.db_file, task_deps_stmt)
        bdb.create_table(self.db_file, task_rst_stmt)

    def create_workflow(self, workflow: Workflow):
        """Create a workflow in the db"""
        wf_stmt = """INSERT INTO workflow (id, name, state, workdir, main_cwl, wf_path, yaml, reqs, hints, restart)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        wf_input_stmt = """INSERT INTO workflow_input (id, workflow_id, type, value)
                           VALUES (?, ?, ?, ?);"""
        wf_output_stmt = """INSERT INTO workflow_output (id, workflow_id, type, value, source)
                            VALUES (?, ?, ?, ?, ?);"""


        hints_json = json.dumps((h.model_dump() for h in workflow.hints))
        reqs_json = json.dumps((r.model_dump() for r in workflow.reqs))
        bdb.run(self.db_file, wf_stmt, (workflow.id, workflow.name, workflow.state, workflow.workdir,
                                      workflow.main_cwl, workflow.wf_path, workflow.yaml,
                                      reqs_json, hints_json, 0))


        for inp in workflow.inputs:
            bdb.run(self.db_file, wf_input_stmt, (inp.id, workflow.id, inp.type, inp.value))
        for outp in workflow.outputs:
            bdb.run(self.db_file, wf_output_stmt, (outp.id, workflow.id, outp.type, outp.value, outp.source))

    
    def set_init_task_inputs(self, wf_id: str):
        """Set initial workflow task inputs from workflow inputs or defaults"""
        # find all task_inputs of tasks in the workflow
        # find all workflow_inputs to the workflow
        # Where workflow input value is not null and the task input source is the workflow input id,
        # and set the task input value to the workflow input value
        # one query

        inputs_query = """
            UPDATE task_input
            SET value = (
                SELECT wi.value
                FROM task AS t
                JOIN workflow_input AS wi
                ON wi.workflow_id = t.workflow_id
                WHERE
                    t.workflow_id = :wf_id
                    AND task_input.task_id = t.id
                    AND task_input.source = wi.id
                    AND wi.value IS NOT NULL
            )
            WHERE EXISTS (
                SELECT 1
                FROM task AS t
                JOIN workflow_input AS wi
                ON wi.workflow_id = t.workflow_id
                WHERE
                    t.workflow_id = :wf_id
                    AND task_input.task_id = t.id
                    AND task_input.source = wi.id
                    AND wi.value IS NOT NULL
            );"""
        
        defaults_query = """
            UPDATE task_input
            SET value = default_val
            WHERE
                value IS NULL
                AND default_val IS NOT NULL
                AND EXISTS (
                    SELECT 1
                    FROM task AS t
                    JOIN workflow_input AS wi
                    ON wi.workflow_id = t.workflow_id
                    WHERE
                        t.workflow_id = :wf_id
                        AND task_input.task_id = t.id
                        AND task_input.source = wi.id
            );"""


        bdb.run(self.db_file, inputs_query, {'wf_id': wf_id})
        bdb.run(self.db_file, defaults_query, {'wf_id': wf_id})

    def set_runnable_tasks_to_ready(self, wf_id: str):
        """Set all tasks with all inputs satisfied to READY state"""
        set_runnable_ready_query = """
            UPDATE task
            SET state = 'READY'
            WHERE workflow_id = :wf_id
            AND state = 'WAITING'
            AND NOT EXISTS (
                SELECT 1
                FROM task_input AS ti
                WHERE ti.task_id = task.id
                    AND ti.value IS NULL
        );"""
        bdb.run(self.db_file, set_runnable_ready_query, {'wf_id': wf_id})

    def set_workflow_state(self, wf_id: str, state: str):
        """Set the state of the workflow."""
        set_wf_state_query = """
            UPDATE workflow
            SET state = :state
            WHERE id = :wf_id;"""
        bdb.run(self.db_file, set_wf_state_query, {'wf_id': wf_id, 'state': state})

    def create_task(self, task: Task):
        """Create a task in the db"""
        task_stmt = """INSERT INTO task (id, workflow_id, name, state, workdir, base_command, stdout, stderr, reqs, hints, metadata)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        task_input_stmt = """INSERT INTO task_input (id, task_id, type, value, default_val, source, prefix, position, value_from)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        task_output_stmt = """INSERT INTO task_output (id, task_id, type, value, glob)
                            VALUES (?, ?, ?, ?, ?);"""


        hints_json = json.dumps((h.model_dump() for h in task.hints))
        reqs_json = json.dumps((r.model_dump() for r in task.reqs))
        metadata_json = json.dumps(task.metadata)
        bdb.run(self.db_file, task_stmt, (task.id, task.workflow_id, task.name, task.state, task.workdir,
                                      json.dumps(task.base_command), task.stdout, task.stderr,
                                      reqs_json, hints_json, metadata_json))


        for inp in task.inputs:
            bdb.run(self.db_file, task_input_stmt, (inp.id, task.id, inp.type, inp.value,
                                                    inp.default_val, inp.source,
                                                    inp.prefix, inp.position,
                                                    inp.value_from))
        for outp in task.outputs:
            bdb.run(self.db_file, task_output_stmt, (outp.id, task.id, outp.type,
                                                     outp.value, outp.glob))
    
    def set_task_state(self, task_id: str, state: str):
        """Set the state of a task."""
        set_task_state_query = """
            UPDATE task
            SET state = :state
            WHERE id = :task_id;"""
        bdb.run(self.db_file, set_task_state_query, {'task_id': task_id, 'state': state})


    def add_dependencies(self, task: Task, old_task: Task=None, restarted_task=False):
        """Add dependencies for a task based on its inputs and outputs."""
        if restarted_task:
            set_restarted_wf = """
                UPDATE workflow
                SET restart = 1
                WHERE id = :wf_id;"""
            delete_dependencies_query = """
                DELETE FROM task_dep
                WHERE depends_on_task_id = :depends_on_task_id;"""

            restarted_query = """
                INSERT INTO task_restart (restarting_task_id, restarted_from_task_id)
                VALUES (:restarting_task_id, :restarted_from_task_id);"""

            dependency_query = """
                INSERT OR IGNORE INTO task_dep (depending_task_id, depends_on_task_id)
                SELECT DISTINCT t.id AS depending_task_id, s.id AS depends_on_task_id
                FROM task AS s
                JOIN task_output AS o
                    ON o.task_id = s.id
                JOIN task_input AS i
                    ON i.source = o.id
                JOIN task AS t
                    ON t.id = i.task_id
                WHERE
                    s.id = :task_id
                    AND s.workflow_id = t.workflow_id;"""
            bdb.run(self.db_file, set_restarted_wf, {'wf_id': task.workflow_id})
            bdb.run(self.db_file, delete_dependencies_query, {'depends_on_task_id': old_task.id})
            bdb.run(self.db_file, restarted_query, {'restarting_task_id': task.id,
                                                     'restarted_from_task_id': old_task.id})
            bdb.run(self.db_file, dependency_query, {'task_id': task.id})
        else:
            dependency_query = """
                INSERT OR IGNORE INTO task_dep (depending_task_id, depends_on_task_id)
                SELECT DISTINCT s.id AS depending_task_id, t.id AS depends_on_task_id
                FROM task AS s
                JOIN task_input AS i
                ON i.task_id = s.id
                JOIN task_output AS o
                ON o.id = i.source
                JOIN task AS t
                ON t.id = o.task_id
                WHERE
                    s.id = :task_id
                    AND s.workflow_id = t.workflow_id;"""
            
            dependent_query = """
                INSERT OR IGNORE INTO task_dep (depending_task_id, depends_on_task_id)
                SELECT DISTINCT t.id AS depending_task_id, s.id AS depends_on_task_id
                FROM task AS s
                JOIN task_output AS o
                ON o.task_id = s.id
                JOIN task_input AS i
                ON i.source = o.id
                JOIN task AS t
                ON t.id = i.task_id
                WHERE
                    s.id = :task_id
                    AND s.workflow_id = t.workflow_id;"""

            bdb.run(self.db_file, dependency_query, {'task_id': task.id})
            bdb.run(self.db_file, dependent_query, {'task_id': task.id})


    def copy_task_outputs(self, task: Task):
        """Use task outputs to set dependent task inputs or workflow outputs

        or set dependent task inputs to default if necessary"""

        task_inputs_query = """
            UPDATE task_input
            SET value = (
                SELECT o.value
                FROM task_dep AS d
                JOIN task_output AS o
                ON o.task_id = d.depends_on_task_id
                WHERE
                    d.depends_on_task_id     = :task_id
                    AND d.depending_task_id = task_input.task_id
                    AND task_input.source = o.id
                    AND o.value IS NOT NULL
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM task_dep AS d
                JOIN task_output AS o
                ON o.task_id = d.depends_on_task_id
                WHERE
                    d.depends_on_task_id      = :task_id
                    AND d.depending_task_id = task_input.task_id
                    AND task_input.source = o.id
                    AND o.value IS NOT NULL
            );"""
        
        defaults_query = """
            UPDATE task_input
            SET value = default_val
            WHERE
                value IS NULL
                AND default_val IS NOT NULL
                AND EXISTS (
                    SELECT 1
                    FROM task_dep AS d_down
                    WHERE
                        d_down.depending_task_id = task_input.task_id
                        AND d_down.depends_on_task_id = :task_id
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM task_dep AS d_up
                    JOIN task AS pt
                    ON pt.id = d_up.depends_on_task_id
                    WHERE
                        d_up.depending_task_id = task_input.task_id
                        AND pt.state != 'COMPLETED'
                );"""
        
        workflow_output_query = """
            UPDATE workflow_output
            SET value = (
                SELECT o.value
                FROM task_output AS o
                WHERE
                    o.id = workflow_output.source
                    AND o.task_id = :task_id
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1
                FROM task_output AS o
                WHERE
                    o.id = workflow_output.source
                    AND o.task_id = :task_id
            );"""
        
        bdb.run(self.db_file, task_inputs_query, {'task_id': task.id})
        bdb.run(self.db_file, defaults_query, {'task_id': task.id})
        bdb.run(self.db_file, workflow_output_query, {'task_id': task.id})
