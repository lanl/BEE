from beeflow.common.cwl.workflow import (
    Task,
    Input,
    Output,
    Workflow,
    MPI,
    Charliecloud,
    Slurm,
    Script,
)
from importlib.resources import files

examples = files("beeflow.common.cwl.examples")


def test_workflow_cat_grep_tar(tmpdir):
    """Regression test of cat-grep-tar example."""
    expected_wf = examples / "cat-grep-tar" / "cat-grep-tar.cwl"
    expected_yaml = examples / "cat-grep-tar" / "cat-grep-tar.yml"
    cat = Task(
        name="cat",
        base_command="cat",
        stdout="cat.txt",
        stderr="cat.err",
        # Position is just where the argument is in the argument list
        # So for this example it's cat lorem.txt
        inputs=[Input("input_file", "File", "lorem.txt", position=1)],
        outputs=[
            Output("contents", "stdout"),
            Output("cat_stderr", "stderr", source="cat/cat_stderr"),
        ],
    )

    grep0 = Task(
        name="grep0",
        base_command="grep",
        stdout="occur0.txt",
        inputs=[
            Input("word0", "string", "Vivamus", position=1),
            # This task takes the contents output from the previous task as input
            Input("text_file", "File", "cat/contents", position=2),
        ],
        outputs=[Output("occur", "stdout")],
    )

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

    tar = Task(
        name="tar",
        base_command="tar",
        stdout="occur1.txt",
        inputs=[
            Input("tarball_fname", "string", "out.tgz", position=1, prefix="-cf"),
            Input("file0", "File", "grep0/occur", position=2),
            Input("file1", "File", "grep1/occur", position=3),
        ],
        # Glob is used to check the filename for the output
        outputs=[
            Output(
                "tarball", "File", glob="$(inputs.tarball_fname)", source="tar/tarball"
            )
        ],
    )

    workflow = Workflow("cat-grep-tar", [cat, grep0, grep1, tar])
    with tmpdir.as_cwd():
        workflow.write_wf(".")
        workflow.write_yaml(".")
        with open("cat-grep-tar.cwl", "r") as f1, open(expected_wf, "r") as f2:
            actual = f1.read()
            expected = f2.read()
            assert actual == expected
        with open("cat-grep-tar.yml", "r") as f1, open(expected_yaml, "r") as f2:
            actual = f1.read()
            expected = f2.read()
            assert actual == expected


def test_workflow_comd(tmpdir):
    """Regression test of comd example."""
    expected_wf = examples / "comd" / "comd.cwl"
    expected_yaml = examples / "comd" / "comd.yml"
    comd_task = Task(
        name="comd",
        base_command="/CoMD/bin/CoMD-mpi -e",
        stdout="comd.txt",
        stderr="comd.err",
        # list of Input objects
        # The 2s and 40s are the actual value we want these to be
        # this is how one sets input parameters. Prefix is just the
        inputs=[
            Input("i", "int", 2, prefix="-i"),
            Input("j", "int", 2, prefix="-j"),
            Input("k", "int", 2, prefix="-k"),
            Input("x", "int", 40, prefix="-x"),
            Input("y", "int", 40, prefix="-y"),
            Input("z", "int", 40, prefix="-z"),
            Input("pot_dir", "string", "/CoMD/pots", prefix="--potDir"),
        ],
        # List of Output objects.
        # In this case we just have a file that represents stdout.
        # The important part here is the source field that states
        #   this output comes from this task
        outputs=[Output("comd_stdout", "File", source="comd/comd_stdout")],
        hints=[
            # The slurm requirement
            MPI(nodes=4, ntasks=8),
            # Example of slurm options
            # Slurm(account="standard", time_limit=60, partition="standard",
            #      qos="debug", reservation="standard"),
            Script(pre_script="comd_pre.sh"),
            Slurm(time_limit=500),
            Charliecloud(
                docker_file="Dockerfile.comd-x86_64", container_name="comd-mpi"
            ),
        ],
    )
    workflow = Workflow("comd", [comd_task])
    with tmpdir.as_cwd():
        workflow.write_wf(".")
        workflow.write_yaml(".")
        with open("comd.cwl", "r") as f1, open(expected_wf, "r") as f2:
            actual = f1.read()
            expected = f2.read()
            assert actual == expected
        with open("comd.yml", "r") as f1, open(expected_yaml, "r") as f2:
            actual = f1.read()
            expected = f2.read()
            assert actual == expected
