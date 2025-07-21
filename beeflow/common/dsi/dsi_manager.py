"""Contains the DSI manager for workflow histories"""
import json
import re
import importlib.resources
from dsi.dsi import DSI

from beeflow.common.paths import workdir

_SQLITE_RESERVED = {
    "ABORT","ADD","ALL","AND","AS","ASC","BY","CASE","CHECK","CREATE",
    "DEFAULT","DELETE","DESC","DISTINCT","DROP","ELSE","FROM","GROUP",
    "HAVING","IN","INDEX","INSERT","INTO","IS","JOIN","LIMIT","NOT",
    "NULL","ON","OR","ORDER","PRIMARY","SELECT","SET","TABLE","THEN",
    "UNION","UPDATE","VALUES","WHEN","WHERE"
}

_clean_re = re.compile(r"[^A-Za-z0-9_]")

def clean_key(k: str) -> str:
    """
    Turn an arbitrary JSON key into a SQLite-safe column name.

    • replaces every bad character with '_'  
    • prefixes keys that start with a digit with '_'  
    • appends '_col' when the cleaned key is a reserved word
    """
    k = _clean_re.sub("_", k)
    if k and k[0].isdigit():
        k = "_"+k
    if k.upper() in _SQLITE_RESERVED:
        k = f"{k}_col"
    return k



class DSIManager:
    """Manager for the DSI (Data Storage Interface) used in Beeflow."""
    def __init__(self):
        self.dsi = DSI(f'{workdir()}/bee.db')
        with importlib.resources.path("beeflow.common.dsi", "schema.json") as schema_path:
            self.dsi.schema(str(schema_path))


    def list_of_dict(self, data, secondary_key, secondary_value):
        """Convert inputs or outputs to list of dict"""
        result = []
        if data:
            for item in data:
                d = {key: value for key, value in item.dict().items() if value is not None}
                d[secondary_key] = secondary_value
                result.append(d)
            return result
        return None


    def store_dict_list(self, data, table_name):
        """Store a list of dicts in the DSI"""
        if not data:
            return
        for datum in data:
            safe_row = {clean_key(k): v for k, v in datum.items() if v is not None}
            print(safe_row)
            json_file = f'/tmp/{table_name}.json'
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(safe_row, f)
            self.dsi.read(json_file, "JSON", table_name=table_name)


    def save_wf_info(self, wfi):
        """Save workflow information to the DSI."""
        workflow, tasks = wfi.get_workflow()
        # Create temporary json files for info to store
        workflow_dict = {
            "id": workflow.id,
            "name": workflow.name,
            "state": workflow.state,
        }

        wf_input_dict_list = self.list_of_dict(workflow.inputs, "workflow_id", workflow.id)

        wf_output_dict_list = self.list_of_dict(workflow.outputs, "workflow_id", workflow.id)

        wf_requirement_dict_list = []
        for requirement in workflow.requirements:
            wf_requirement_dict = {
                "workflow_id": workflow.id,
                "class_": requirement.class_,
            }
            for key, value in requirement.params.items():
                wf_requirement_dict[key] = value
            wf_requirement_dict_list.append(wf_requirement_dict)

        wf_hint_dict_list = []
        for hint in workflow.hints:
            wf_hint_dict = {
                "workflow_id": workflow.id,
                "class_": hint.class_,
            }
            for key, value in hint.params.items():
                wf_hint_dict[key] = value
            wf_hint_dict_list.append(wf_hint_dict)

        task_dict_list = []
        task_input_dict_list = []
        task_output_dict_list = []
        task_requirement_dict_list = []
        task_hint_dict_list = []
        task_metadata_dict_list = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "name": task.name,
                "workflow_id": workflow.id,
                "state": task.state,
                "base_command": str(task.base_command),
            }
            if task.stdout:
                task_dict["stdout"] = task.stdout
            if task.stderr:
                task_dict["stderr"] = task.stderr
            if task.workdir:
                task_dict["workdir"] = str(task.workdir)
            task_dict_list.append(task_dict)

            task_input_dict_list.extend(
                self.list_of_dict(task.inputs, "task_id", task.id)
            )

            task_output_dict_list.extend(
                self.list_of_dict(task.outputs, "task_id", task.id)
            )

            task.metadata['task_id'] = task.id
            task_metadata_dict_list.append(
                {k: v for k, v in task.metadata.items() if v is not None}
            )

            for requirement in task.requirements:
                task_requirement_dict = {
                    "task_id": task.id,
                    "class_": requirement.class_,
                }
                for key, value in requirement.params.items():
                    task_requirement_dict[key] = value
                task_requirement_dict_list.append(task_requirement_dict)

            for hint in task.hints:
                task_hint_dict = {
                    "task_id": task.id,
                    "class_": hint.class_,
                }
                for key, value in hint.params.items():
                    task_hint_dict[key] = value
                task_hint_dict_list.append(task_hint_dict)

        # make csv files to store in dsi
        self.store_dict_list([workflow_dict], "workflow")
        self.store_dict_list(wf_input_dict_list, "workflow_input")
        self.store_dict_list(wf_output_dict_list, "workflow_output")
        self.store_dict_list(wf_requirement_dict_list, "workflow_requirement")
        self.store_dict_list(wf_hint_dict_list, "workflow_hint")
        self.store_dict_list(task_dict_list, "task")
        self.store_dict_list(task_input_dict_list, "task_input")
        self.store_dict_list(task_output_dict_list, "task_output")
        self.store_dict_list(task_requirement_dict_list, "task_requirement")
        self.store_dict_list(task_hint_dict_list, "task_hint")
        self.store_dict_list(task_metadata_dict_list, "task_metadata")


dsi_manager = DSIManager()
