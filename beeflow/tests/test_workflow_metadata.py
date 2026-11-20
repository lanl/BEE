"""Canonical workflow metadata and legacy model/storage compatibility."""

from pathlib import Path
import sqlite3

import pytest

from beeflow.common.object_models import Workflow
from beeflow.common.db.gdb_db import SQL_GDB
from beeflow.common.gdb import neo4j_cypher, neo4j_driver


@pytest.mark.parametrize("legacy", [False, True])
def test_workflow_metadata_aliases(legacy):
    fields = ({"main_cwl": "workflow.py", "yaml": "job.json"} if legacy else
              {"spec_file": "workflow.py", "job_file": "job.json"})
    workflow = Workflow(id="wf", name="example", format_name="python", **fields)
    assert workflow.spec_file == workflow.main_cwl == "workflow.py"
    assert workflow.job_file == workflow.yaml == "job.json"
    canonical = workflow.model_dump()
    assert canonical["spec_file"] == "workflow.py"
    assert "main_cwl" not in canonical and "yaml" not in canonical
    wire = workflow.model_dump(by_alias=True, mode="json")
    assert wire["main_cwl"] == "workflow.py"
    assert wire["yaml"] == "job.json"
    assert "spec_file" not in wire and "job_file" not in wire
    assert Workflow.model_validate(wire).model_dump() == canonical
    workflow.main_cwl = Path("other.yaml")
    workflow.yaml = None
    assert workflow.spec_file == Path("other.yaml")
    assert workflow.job_file is None
    assert workflow.model_dump(by_alias=True, mode="json")["main_cwl"] == "other.yaml"


def test_canonical_fields_take_precedence():
    workflow = Workflow(id="wf", name="example", spec_file="new.py", main_cwl="old.cwl",
                        job_file=None, yaml="old.yml")
    assert workflow.spec_file == "new.py"
    assert workflow.job_file is None


@pytest.mark.parametrize("old_schema", [False, True])
def test_sqlite_workflow_metadata(tmp_path, old_schema):
    filename = str(tmp_path / "graph.db")
    if old_schema:
        with sqlite3.connect(filename) as connection:
            connection.execute("""CREATE TABLE workflow (
                id TEXT PRIMARY KEY, name TEXT, state TEXT, workdir TEXT, main_cwl TEXT,
                wf_path TEXT, yaml TEXT, reqs JSON, hints JSON, restart INTEGER DEFAULT 0)""")
            connection.execute("""INSERT INTO workflow VALUES
                ('old', 'legacy', 'Running', '/work', 'old.cwl', '/source', 'job.yml',
                 '[]', '[]', 1)""")
    database = SQL_GDB(filename)
    if old_schema:
        old = database.get_workflow("old")
        assert old.spec_file == "old.cwl"
        assert old.job_file == "job.yml"
        assert old.format_name is None
        assert old.state == "Running"
    workflow = Workflow(id="new", name="new", spec_file="nested/workflow.yaml",
                        job_file="inputs/job.json", format_name="yaml")
    database.create_workflow(workflow)
    assert database.get_workflow("new").model_dump() == workflow.model_dump()
    SQL_GDB(filename)  # The migration is idempotent and preserves existing records.
    with sqlite3.connect(filename) as connection:
        row = connection.execute(
            "SELECT main_cwl, yaml, format_name FROM workflow WHERE id = 'new'"
        ).fetchone()
    assert row == ("nested/workflow.yaml", "inputs/job.json", "yaml")


@pytest.mark.parametrize("canonical", [False, True])
def test_neo4j_workflow_metadata(canonical):
    record = {"id": "wf", "name": "workflow", "state": "Running", "workdir": "/work",
              "wf_path": "/source", "main_cwl": "old.cwl", "yaml": "old.yml"}
    if canonical:
        record.update(spec_file="nested/new.yaml", job_file="job.json", format_name="yaml")
    workflow = neo4j_driver._reconstruct_workflow(record, [], [], [], [])
    assert workflow.spec_file == ("nested/new.yaml" if canonical else "old.cwl")
    assert workflow.job_file == ("job.json" if canonical else "old.yml")
    assert workflow.format_name == ("yaml" if canonical else None)


def test_neo4j_writes_legacy_and_canonical_metadata(mocker):
    transaction = mocker.Mock()
    workflow = Workflow(id="wf", name="example", spec_file="workflow.py", job_file="job.yml",
                        format_name="python")
    neo4j_cypher.create_workflow_node(transaction, workflow)
    query = transaction.run.call_args.args[0]
    assert "w.spec_file = $main_cwl" in query
    assert "w.job_file = $yaml" in query
    assert "w.main_cwl = $main_cwl" in query
    assert "w.format_name = $format_name" in query
    assert transaction.run.call_args.kwargs["format_name"] == "python"


def test_integration_runner_submission_arguments(tmp_path, mocker):
    from beeflow.common.integration.utils import Workflow as IntegrationWorkflow
    package = mocker.patch("beeflow.client.bee_client.package")
    submit = mocker.patch("beeflow.client.bee_client.submit", return_value="wf-id")
    workflow = IntegrationWorkflow("example", tmp_path / "source", "workflow.cwl", "job.yml",
                                   tmp_path / "work", [])
    workflow.run()
    package.assert_called_once_with(tmp_path / "source", tmp_path)
    submit.assert_called_once_with(
        tmp_path / "source.tgz", name="example", main_cwl="workflow.cwl", job="job.yml",
        workdir=tmp_path / "work", no_start=False,
    )
    assert workflow.wf_id == "wf-id"
