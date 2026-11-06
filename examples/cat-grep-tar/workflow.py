"""Cat-grep-tar workflow written with the new BEE python workflow API.

This example shows the CWL-free way of describing a BEE workflow: build a
Workflow object with the classes from beeflow.common.workflow_api and hand it
to the BeeParser, which converts it directly into the Workflow and Task
objects loaded into the graph database by the WorkflowInterface. No CWL is
generated or parsed.

Run it directly to see the parsed result:

    python3 workflow.py

Submit it to a running BEE instance with:

    beeflow submit workflow.py
"""
from beeflow.common.workflow_api import Workflow, Resources

workflow = Workflow(
    name="cat-grep-tar",
    description="Cat an input file, grep it two ways, and tar the results",
)

# {name} placeholders in a command are filled in at execution time from the
# task's params and inputs. 'cat' copies the input file to cat.txt.
cat = workflow.add_task(
    name="cat",
    commands=["cat {input_file}"],
    inputs={"input_file": "lorem.txt"},
    stdout="cat.txt",
    stderr="cat.err",
    # outputs map output names to the files they collect
    outputs={"contents": "cat.txt", "cat_stderr": "cat.err"},
)

# task.output("name") creates a dependency on another task
grep0 = workflow.add_task(
    name="grep0",
    commands=["grep {word0} {text_file}"],
    params={"word0": "Vivamus"},
    inputs={"text_file": cat.output("contents")},
    stdout="occur0.txt",
    outputs={"occur": "occur0.txt"},
)

grep1 = workflow.add_task(
    name="grep1",
    commands=["grep {word1} {text_file}"],
    params={"word1": "pulvinar"},
    inputs={"text_file": cat.output("contents")},
    stdout="occur1.txt",
    outputs={"occur": "occur1.txt"},
)

tar = workflow.add_task(
    name="tar",
    commands=["tar -cf {tarball_fname} {file0} {file1}"],
    inputs={
        "tarball_fname": "out.tgz",
        "file0": grep0.output("occur"),
        "file1": grep1.output("occur"),
    },
    # resources and scheduler_options replace the old MPI/Slurm hints
    resources=Resources(nodes=1, ntasks=1, walltime="01:00:00"),
    scheduler_options={"account": "standard", "partition": "standard"},
    outputs={"tarball": "out.tgz"},
)


if __name__ == "__main__":
    from beeflow.common.parser import BeeParser

    # Parse the specification directly into the objects used by the
    # WorkflowInterface (no CWL is generated).
    parser = BeeParser()
    wf, tasks = parser.parse_workflow("example", workflow.name, workflow)

    print("Parsed workflow inputs:")
    for input_ in wf.inputs:
        print(f"  {input_.id} ({input_.type}) = {input_.value}")
    print("Parsed workflow outputs:")
    for output in wf.outputs:
        print(f"  {output.id} ({output.type}) from {output.source}")
    print("Parsed tasks:")
    for task in tasks:
        # Fill in the placeholder values so the full command can be shown
        for input_ in task.inputs:
            if input_.value is None:
                # Sourced inputs are filled in at runtime by BEE
                input_.value = (
                    input_.default if input_.default is not None
                    else f"<{input_.source}>"
                )
        print(f"  {task.name}: {' '.join(task.command)}")
        for output in task.outputs:
            print(f"    output {output.id} (glob: {output.glob})")
