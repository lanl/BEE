"""Contains the DSI manager for workflow histories"""
from dsi.dsi import DSI
from beeflow.common.paths import workdir
import json


class DSIManager:
    """Manager for the DSI (Data Storage Interface) used in Beeflow."""
    def __init__(self):
        self.dsi = DSI(f'{workdir()}/bee.db')
        self.dsi.schema("schema.json")

    def save_wf_info(self, wfi):
        """Save workflow information to the DSI."""
        workflow, tasks = wfi.get_workflow()
        # Create temporary json files for info to store
        workflow_dict = {
            "id": workflow.id,
            "name": workflow.name,
            "state": workflow.state,
        }

        task_dict_list = [{
            "id": task.id,
            "name": task.name,
            "state": task.state,
            "stdout": task.stdout,
            "stderr": task.stderr,
            "workdir": str(task.workdir),
            "workflow_id": workflow.id
        } for task in tasks]

        # make json file that is just the workflow dict
        workflow_json = f'/tmp/{workflow.id}_workflow.json'
        with open(workflow_json, 'w', encoding='utf-8') as f:
            json.dump(workflow_dict, f)
        self.dsi.read(workflow_json, "JSON", table_name="workflow")

        for task in task_dict_list:
            task_json = f'/tmp/{task["id"]}_task.json'
            with open(task_json, 'w', encoding='utf-8') as f:
                json.dump(task, f)
            self.dsi.read(task_json, "JSON", table_name="task")


dsi_manager = DSIManager()
