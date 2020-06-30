import sys
from beeflow.common.wf_interface import WorkflowInterface

try:
    wf = WorkflowInterface(userconfig=sys.argv[1])
except KeyError:
    wf = WorkflowInterface()

tasks = [
    wf.create_task("Echo", command=["echo", "test"]),
    wf.create_task("Echo", command=["echo", "test"])
]

workflow = wf.create_workflow(
        tasks=tasks,
        requirements={wf.create_requirement("ResourceRequirement", "ramMin", 1024)},
        hints={wf.create_requirement("ResourceRequirement", "ramMax", 2048)}
)

load_workflow(workflow)

