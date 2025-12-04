"""Graph Database SQL implementation."""

import json
from typing import Optional
from beeflow.common.db import bdb
from beeflow.common.object_models import (Workflow, Task, Requirement, Hint, 
InputParameter, OutputParameter, StepInput, StepOutput)
from beeflow.wf_manager.models import WorkflowInfo

failed_task_states = ['FAILED', 'SUBMIT_FAIL', 'BUILD_FAIL', 'DEP_FAIL', 'TIMEOUT', 'CANCELLED']
final_task_states = ['COMPLETED', 'RESTARTED'] + failed_task_states

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
            id TEXT,
            workflow_id TEXT,
            type TEXT,
            value TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE,
            PRIMARY KEY (workflow_id , id)
        );"""

        wf_outputs_stmt = """CREATE TABLE IF NOT EXISTS workflow_output (
            id TEXT,
            workflow_id TEXT,
            type TEXT,
            value TEXT,
            source TEXT,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE,
            PRIMARY KEY (workflow_id , id)
        );"""

        tasks_stmt = """CREATE TABLE IF NOT EXISTS task (
            id TEXT PRIMARY KEY,
            workflow_id TEXT,
            name TEXT,
            state TEXT,
            workdir TEXT,
            base_command JSON,
            stdout TEXT,
            stderr TEXT,
            reqs JSON,
            hints JSON,
            metadata JSON,
            FOREIGN KEY (workflow_id) REFERENCES workflow(id) ON DELETE CASCADE
        );"""

        task_inputs_stmt = """CREATE TABLE IF NOT EXISTS task_input (
            id TEXT,
            task_id TEXT,
            type TEXT,
            value TEXT,
            default_val TEXT,
            source TEXT,
            prefix TEXT,
            position INTEGER,
            value_from TEXT,
            FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
            PRIMARY KEY (task_id, id)
        );"""

        task_outputs_stmt = """CREATE TABLE IF NOT EXISTS task_output (
            id TEXT,
            task_id TEXT,
            type TEXT,
            value TEXT,
            glob TEXT,
            FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE,
            PRIMARY KEY (task_id, id)
        );"""

        task_deps_stmt = """CREATE TABLE IF NOT EXISTS task_dep (
                depending_task_id TEXT NOT NULL,
                depends_on_task_id   TEXT NOT NULL,
                PRIMARY KEY (depending_task_id, depends_on_task_id),
                FOREIGN KEY (depending_task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (depends_on_task_id)   REFERENCES task(id) ON DELETE CASCADE
        );"""

        task_rst_stmt = """CREATE TABLE IF NOT EXISTS task_restart (
                restarting_task_id TEXT NOT NULL,
                restarted_from_task_id   TEXT NOT NULL,
                PRIMARY KEY (restarting_task_id, restarted_from_task_id),
                FOREIGN KEY (restarting_task_id) REFERENCES task(id) ON DELETE CASCADE,
                FOREIGN KEY (restarted_from_task_id)   REFERENCES task(id) ON DELETE CASCADE
        );"""

        add_indexes_stmt = """CREATE INDEX IF NOT EXISTS idx_task_wf_id ON task(workflow_id);
                CREATE INDEX IF NOT EXISTS idx_task_wf_state ON task(workflow_id, state);

                CREATE INDEX IF NOT EXISTS idx_task_input_task_id ON task_input(task_id);
                CREATE INDEX IF NOT EXISTS idx_task_output_task_id ON task_output(task_id);

                CREATE INDEX IF NOT EXISTS idx_task_dep_depends_on ON task_dep(depends_on_task_id);
                CREATE INDEX IF NOT EXISTS idx_task_dep_depending ON task_dep(depending_task_id);
        """

        bdb.create_table(self.db_file, wfs_stmt)
        bdb.create_table(self.db_file, wf_inputs_stmt)
        bdb.create_table(self.db_file, wf_outputs_stmt)
        bdb.create_table(self.db_file, tasks_stmt)
        bdb.create_table(self.db_file, task_inputs_stmt)
        bdb.create_table(self.db_file, task_outputs_stmt)
        bdb.create_table(self.db_file, task_deps_stmt)
        bdb.create_table(self.db_file, task_rst_stmt)
        bdb.run(self.db_file, add_indexes_stmt)

    def create_workflow(self, workflow: Workflow):
        """Create a workflow in the db"""
        wf_stmt = """INSERT INTO workflow (id, name, state, workdir, main_cwl,
                    wf_path, yaml, reqs, hints, restart)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        wf_input_stmt = """INSERT INTO workflow_input (id, workflow_id, type, value)
                           VALUES (?, ?, ?, ?);"""
        wf_output_stmt = """INSERT INTO workflow_output (id, workflow_id, type, value, source)
                            VALUES (?, ?, ?, ?, ?);"""


        hints_json = json.dumps([h.model_dump() for h in workflow.hints])
        reqs_json = json.dumps([r.model_dump() for r in workflow.requirements])
        bdb.run(self.db_file, wf_stmt, (workflow.id, workflow.name, workflow.state,
                                        workflow.workdir, workflow.main_cwl, workflow.wf_path,
                                        workflow.yaml, reqs_json, hints_json, 0))


        for inp in workflow.inputs:
            bdb.run(self.db_file, wf_input_stmt, (inp.id, workflow.id, inp.type, inp.value))
        for outp in workflow.outputs:
            bdb.run(self.db_file, wf_output_stmt, (outp.id, workflow.id, outp.type,
                                                   outp.value, outp.source))


    def set_init_task_inputs(self, wf_id: str):
        """Set initial workflow task inputs from workflow inputs or defaults"""

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
        task_stmt = """INSERT INTO task (id, workflow_id, name, state, workdir, base_command,
                    stdout, stderr, reqs, hints, metadata)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        task_input_stmt = """INSERT INTO task_input (id, task_id, type, value, default_val, source,
                    prefix, position, value_from)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        task_output_stmt = """INSERT INTO task_output (id, task_id, type, value, glob)
                            VALUES (?, ?, ?, ?, ?);"""


        hints_json = json.dumps([h.model_dump() for h in task.hints])
        reqs_json = json.dumps([r.model_dump() for r in task.requirements])
        metadata_json = json.dumps(task.metadata)
        bdb.run(self.db_file, task_stmt, (task.id, task.workflow_id, task.name, 
                                          task.state, task.workdir,
                                      json.dumps(task.base_command), task.stdout, task.stderr,
                                      reqs_json, hints_json, metadata_json))


        for inp in task.inputs:
            bdb.run(self.db_file, task_input_stmt, (inp.id, task.id, inp.type, inp.value,
                                                    inp.default, inp.source,
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

        defaults_query = f"""
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
                        AND pt.state NOT IN ({', '.join(['?' for _ in final_task_states])})
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


    def get_task(self, task_id: str) -> Optional[Task]:
        """Return a reconstructed Task object from the db by its ID."""
        task_data = bdb.getone(self.db_file, 'SELECT * FROM task WHERE id=?', [task_id])
        if not task_data:
            return None

        task = Task(
            id=task_data[0],
            workflow_id=task_data[1],
            name=task_data[2],
            state=task_data[3],
            workdir=task_data[4],
            base_command=json.loads(task_data[5]),
            stdout=task_data[6],
            stderr=task_data[7],
            requirements=[Requirement.model_validate(r) for r in json.loads(task_data[8])],
            hints=[Hint.model_validate(h) for h in json.loads(task_data[9])],
            metadata=json.loads(task_data[10]),
            inputs=self.get_task_inputs(task_data[0]),
            outputs=self.get_task_outputs(task_data[0])
            )
        return task

    def get_task_inputs(self, task_id: str):
        """Return a list of StepInput objects for a task."""
        task_inputs = bdb.getall(self.db_file, 'SELECT * FROM task_input WHERE task_id=?',
                                 [task_id])
        return [StepInput(
            id=ti[0],
            type=ti[2],
            value=ti[3],
            default=ti[4],
            source=ti[5],
            prefix=ti[6],
            position=ti[7],
            value_from=ti[8]
        )
        for ti in task_inputs] if task_inputs else []

    def get_task_outputs(self, task_id: str):
        """Return a list of StepOutput objects for a task."""
        task_outputs = bdb.getall(self.db_file, 'SELECT * FROM task_output WHERE task_id=?',
                                  [task_id])
        return [StepOutput(
            id=to[0],
            type=to[2],
            value=to[3],
            glob=to[4]
        )
        for to in task_outputs] if task_outputs else []

    def get_all_workflow_info(self):
        """Return a list of all workflows in the db.

        :rtype: list of WorkflowInfo
        """
        wf_data = bdb.getall(self.db_file, 'SELECT id, name, state FROM workflow')
        wf_info_list = [WorkflowInfo(
            wf_id=wf[0],
            wf_name=wf[1],
            wf_status=wf[2],
        ) for wf in wf_data] if wf_data else []
        return wf_info_list


    def get_workflow(self, wf_id: str) -> Optional[Workflow]:
        """Return a reconstructed Workflow object from the db by its ID."""
        wf_data = bdb.getone(self.db_file, 'SELECT * FROM workflow WHERE id=?', [wf_id])
        if not wf_data:
            return None

        workflow_object = Workflow(
            id=wf_data[0],
            name=wf_data[1],
            state=wf_data[2],
            workdir=wf_data[3],
            main_cwl=wf_data[4],
            wf_path=wf_data[5],
            yaml=wf_data[6],
            requirements=[Requirement.model_validate(r) for r in json.loads(wf_data[7])],
            hints=[Hint.model_validate(h) for h in json.loads(wf_data[8])],
            inputs=self.get_workflow_inputs(wf_data[0]),
            outputs=self.get_workflow_outputs(wf_data[0])
        )
        return workflow_object

    def get_workflow_inputs(self, wf_id: str):
        """Return a list of InputParameter objects for a workflow."""
        wf_inputs = bdb.getall(self.db_file, 'SELECT * FROM workflow_input WHERE workflow_id=?',
                               [wf_id])
        return [InputParameter(
            id=wi[0],
            type=wi[2],
            value=wi[3]
        )
        for wi in wf_inputs] if wf_inputs else []

    def get_workflow_outputs(self, wf_id: str):
        """Return a list of OutputParameter objects for a workflow."""
        wf_outputs = bdb.getall(self.db_file, 'SELECT * FROM workflow_output WHERE workflow_id=?',
                                [wf_id])
        return [OutputParameter(
            id=wo[0],
            type=wo[2],
            value=wo[3],
            source=wo[4]
        )
        for wo in wf_outputs] if wf_outputs else []

    def get_workflow_state(self, wf_id: str) -> str:
        """Return the state of a workflow."""
        state = bdb.getone(self.db_file, 'SELECT state FROM workflow WHERE id=?', [wf_id])
        return state[0] if state else None

    def get_workflow_requirements_and_hints(self, wf_id: str):
        """Return all workflow requirements and hints from the db.

        Must return a tuple with the format (requirements, hints)

        :rtype: (list of Requirement, list of Hint)
        """
        wf_data = bdb.getone(self.db_file, 'SELECT reqs, hints FROM workflow WHERE id=?', [wf_id])
        if not wf_data:
            return ([], [])

        requirements = [Requirement.model_validate(r) for r in json.loads(wf_data[0])]
        hints = [Hint.model_validate(h) for h in json.loads(wf_data[1])]
        return (requirements, hints)

    def get_workflow_tasks(self, wf_id: str):
        """Return a list of all workflow tasks from the db.

        :rtype: list of Task
        """
        tasks_data = bdb.getall(self.db_file, 'SELECT id FROM task WHERE workflow_id=?', [wf_id])
        tasks = [self.get_task(t[0]) for t in tasks_data] if tasks_data else []
        return tasks

    def get_ready_tasks(self, wf_id: str):
        """Return tasks with state 'READY' from the db.

        :rtype: list of Task
        """
        tasks_data = bdb.getall(self.db_file, 
                                "SELECT id FROM task WHERE workflow_id=? AND state='READY'", 
                                [wf_id])
        tasks = [self.get_task(t[0]) for t in tasks_data] if tasks_data else []
        return tasks

    def get_dependent_tasks(self, task_id: str):
        """Return the dependent tasks of a workflow task in the db.

        :param task_id: the id of the task to get dependents for
        :type task_id: str
        :rtype: list of Task
        """
        deps_data = bdb.getall(self.db_file, 
                               "SELECT depending_task_id FROM task_dep WHERE depends_on_task_id=?", 
                               [task_id])
        deps = [self.get_task(d[0]) for d in deps_data] if deps_data else []
        return deps

    def get_task_state(self, task_id: str):
        """Return the state of a task in the db.

        :param task_id: the id of the task to get the state for
        :type task_id: str
        :rtype: str
        """
        state = bdb.getone(self.db_file, 'SELECT state FROM task WHERE id=?', [task_id])
        return state[0] if state else None

    def get_task_metadata(self, task_id: str):
        """Return the metadata of a task in the db.

        :param task_id: the id of the task to get metadata for
        :type task_id: str
        :rtype: dict
        """
        metadata = bdb.getone(self.db_file, 'SELECT metadata FROM task WHERE id=?', [task_id])
        return json.loads(metadata[0]) if metadata and metadata[0] else {}
    
    def set_task_metadata(self, task_id: str, metadata: dict):
        """Set the metadata of a task in the db.

        :param task_id: the id of the task to set metadata for
        :type task_id: str
        :param metadata: the job description metadata
        :type metadata: dict
        """
        prior_metadata = self.get_task_metadata(task_id)
        prior_metadata.update(metadata)
        metadata_json = json.dumps(prior_metadata)
        bdb.run(self.db_file, 'UPDATE task SET metadata=? WHERE id=?',
                [metadata_json, task_id])

    def get_task_input(self, task_id: str, input_id: str):
        """Get a task input object.

        :param task_id: the id of the task to get the input for
        :type task_id: str
        :param input_id: the id of the input to get
        :type input_id: str
        :rtype: StepInput
        """
        ti_data = bdb.getone(self.db_file,
                             'SELECT * FROM task_input WHERE task_id=? AND id=?',
                             [task_id, input_id])
        if not ti_data:
            return None

        task_input = StepInput(
            id=ti_data[0],
            type=ti_data[2],
            value=ti_data[3],
            default=ti_data[4],
            source=ti_data[5],
            prefix=ti_data[6],
            position=ti_data[7],
            value_from=ti_data[8]
        )
        return task_input

    def set_task_input(self, task_id: str, input_id: str, value: str):
        """Set the value of a task input.

        :param task_id: the id of the task to set the input for
        :type task_id: str
        :param input_id: the id of the input to set
        :type input_id: str
        :param value: the new value for the input
        :type value: str
        """
        bdb.run(self.db_file,
                'UPDATE task_input SET value=? WHERE task_id=? AND id=?',
                [value, task_id, input_id])

    def get_task_output(self, task_id: str, output_id: str):
        """Get a task output object.

        :param task_id: the id of the task to get the output for
        :type task_id: str
        :param output_id: the id of the output to get
        :type output_id: str
        :rtype: StepOutput
        """
        to_data = bdb.getone(self.db_file,
                             'SELECT * FROM task_output WHERE task_id=? AND id=?',
                             [task_id, output_id])
        if not to_data:
            return None

        task_output = StepOutput(
            id=to_data[0],
            type=to_data[2],
            value=to_data[3],
            glob=to_data[4]
        )
        return task_output

    def set_task_output(self, task_id: str, output_id: str, value: str):
        """Set the value of a task output.

        :param task_id: the id of the task to set the output for
        :type task_id: str
        :param output_id: the id of the output to set
        :type output_id: str
        :param value: the new value for the output
        :type value: str
        """
        bdb.run(self.db_file,
                'UPDATE task_output SET value=? WHERE task_id=? AND id=?',
                [value, task_id, output_id])

    def set_task_input_type(self, task_id: str, input_id: str, type_: str):
        """Set the type of a task input.

        :param task_id: the id of the task to set the input type for
        :type task_id: str
        :param input_id: the id of the input to set
        :type input_id: str
        :param type_: the new type for the input
        :type type_: str
        """
        bdb.run(self.db_file,
                'UPDATE task_input SET type=? WHERE task_id=? AND id=?',
                [type_, task_id, input_id])

    def set_task_output_glob(self, task_id: str, output_id: str, glob: str):
        """Set the glob of a task output.

        :param task_id: the id of the task to set the output glob for
        :type task_id: str
        :param output_id: the id of the output to set
        :type output_id: str
        :param glob: the new glob for the output
        :type glob: str
        """
        bdb.run(self.db_file,
                'UPDATE task_output SET glob=? WHERE task_id=? AND id=?',
                [glob, task_id, output_id])

    def final_tasks_completed(self, wf_id: str) -> bool:
        """Determine if a workflow's final tasks have completed.

        A workflow's final tasks have completed if each of its final tasks has finished or failed.

        :param wf_id: the ID of the workflow to check
        :type wf_id: str
        :rtype: bool
        """
        placeholders = ','.join('?' for _ in final_task_states)
        final_tasks_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state NOT IN ({placeholders});
        """

        params = [wf_id, *final_task_states]

        result = bdb.getone(self.db_file, final_tasks_query, params)
        return result is not None and result[0] == 0

    def final_tasks_succeeded(self, wf_id: str) -> bool:
        """Determine if a workflow's final tasks have succeeded.

        A workflow's final tasks have succeeded if each of its final tasks has finished successfully.

        :param wf_id: the ID of the workflow to check
        :type wf_id: str
        :rtype: bool
        """
        placeholders = ','.join('?' for _ in failed_task_states)
        final_tasks_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state IN ({placeholders});
        """

        params = [wf_id, *failed_task_states]

        result = bdb.getone(self.db_file, final_tasks_query, params)
        return self.final_tasks_completed(wf_id) and result is not None and result[0] == 0
    
    def final_tasks_failed(self, wf_id: str) -> bool:
        """Determine if all of a workflow's final tasks have failed.

        :param wf_id: the ID of the workflow to check
        :type wf_id: str
        :rtype: bool
        """
        placeholders = ','.join('?' for _ in failed_task_states) + ',?'
        final_tasks_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state NOT IN ({placeholders});
        """

        params = [wf_id, *failed_task_states, 'RESTARTED']

        result = bdb.getone(self.db_file, final_tasks_query, params)
        return result is not None and result[0] == 0
    
    def cancelled_final_tasks_completed(self, wf_id: str) -> bool:
        """Determine if a cancelled workflow's final tasks have completed.

        All of the workflow's scheduled tasks are completed if each of the final task nodes
        are not in states 'PENDING', 'RUNNING', or 'COMPLETING'.

        :param wf_id: the ID of the workflow to check
        :type wf_id: str
        :rtype: bool
        """
        incomplete_states = ['PENDING', 'RUNNING', 'COMPLETING']
        placeholders = ','.join('?' for _ in incomplete_states)
        final_tasks_query = f"""
            SELECT COUNT(*)
            FROM task
            WHERE workflow_id = ?
            AND state IN ({placeholders});
        """

        params = [wf_id, *incomplete_states]

        result = bdb.getone(self.db_file, final_tasks_query, params)
        return result is not None and result[0] == 0

    def remove_workflow(self, wf_id: str):
        """Remove a workflow and all its associated tasks from the db."""
        delete_wf_query = """
            DELETE FROM workflow
            WHERE id = ?;"""
        bdb.run(self.db_file, delete_wf_query, [wf_id])