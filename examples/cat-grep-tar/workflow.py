"""Cat-grep-tar workflow written with the BEE python workflow description API.

This example shows the new (post-CWL) way of describing a BEE workflow: build
a Workflow object with the classes from beeflow.common.cwl.workflow and hand it
to the BeeParser, which converts it directly into the Workflow and Task objects
loaded into the graph database by the WorkflowInterface. No CWL is generated or
parsed.

Run it directly to see the parsed result:

    python3 workflow.py

Submit it to a running BEE instance with:

    beeflow submit cat-grep-tar . workflow.py input.yml <workdir>
"""
from beeflow.common.cwl.workflow import Task, Input, Output, Workflow

# 'cat' copies the input file to stdout (captured in cat.txt)
cat = Task(
    name="cat",
    base_command="cat",
    stdout="cat.txt",
    stderr="cat.err",
    # Position is where the argument appears in the argument list,
    # so this task runs: cat lorem.txt
    inputs=[Input("input_file", "File", "lorem.txt", position=1)],
    outputs=[
        # 'contents' captures the stdout file and feeds the grep tasks
        Output("contents", "stdout"),
        # A source makes an output visible as a workflow output
        Output("cat_stderr", "stderr", source="cat/cat_stderr"),
    ],
)

# 'grep0' searches the cat output for 'Vivamus'
grep0 = Task(
    name="grep0",
    base_command="grep",
    stdout="occur0.txt",
    inputs=[
        Input("word0", "string", "Vivamus", position=1),
        # An Input value of the form "task/output" depends on another task
        Input("text_file", "File", "cat/contents", position=2),
    ],
    outputs=[Output("occur", "stdout")],
)

# 'grep1' searches the cat output for 'pulvinar'
grep1 = Task(
    name="grep1",
    base_command="grep",
    stdout="occur1.txt",
    inputs=[
        Input("word1", "string", "pulvinar", position=1),
        Input("text_file", "File", "cat/contents", position=2),
    ],
    outputs=[Output("occur", "stdout")],
)

# 'tar' bundles both grep outputs into a tarball
tar = Task(
    name="tar",
    base_command="tar",
    stdout="tar.out",
    inputs=[
        Input("tarball_fname", "string", "out.tgz", position=1, prefix="-cf"),
        Input("file0", "File", "grep0/occur", position=2),
        Input("file1", "File", "grep1/occur", position=3),
    ],
    outputs=[
        Output("tarball", "File", glob="out.tgz", source="tar/tarball")
    ],
)

workflow = Workflow("cat-grep-tar", [cat, grep0, grep1, tar])


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
        print(f"  {task.name}: {task.base_command}")
        for input_ in task.inputs:
            print(f"    input {input_.id} from {input_.source}")
        for output in task.outputs:
            print(f"    output {output.id} (glob: {output.glob})")
