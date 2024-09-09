"""Cat grep tar driver for CWL generator."""
import pathlib
from beeflow.common.cwl.cwl import (CWL, CWLInput, RunInput, Inputs, CWLOutput,
                                    CWLInputs, Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding)


def main():
    """Recreate the COMD workflow."""
    # CWLInputs
    cwl_inputs = CWLInputs([CWLInput("input_file", "File", value="lorem.txt"),
                            CWLInput("word0", "string", value="Vivamus"),
                            CWLInput("word1", "string", value="pulvinar"),
                            CWLInput("tarball_fname", "string", value="out.tgz")
                            ])

    # CWLOutputs
    cwl_outputs = Outputs([CWLOutput("tarball", "File", "tar/tarball"),
                           CWLOutput("cat_stderr", "File", "cat/cat_stderr")])

    # Step Cat
    base_command = "cat"
    stdout = "cat.txt"
    stderr = "cat.err"
    cat_inputs = Inputs([RunInput("input_file", "File", InputBinding(position=1))])
    cat_outputs = Outputs([RunOutput("contents", "stdout"), RunOutput("cat_stderr", "stderr")])
    cat_run = Run(base_command, cat_inputs, cat_outputs, stdout, stderr)
    cat_step = Step("cat", cat_run)

    # Step Grep0
    base_command = "grep"
    stdout = "occur0.txt"
    run_inputs = Inputs([RunInput("word", "string",
                                  InputBinding(position=1), source="word0"),
                         RunInput("text_file", "File",
                                  InputBinding(position=2), source="cat/contents")])
    run_outputs = Outputs([RunOutput("occur", "stdout")])
    grep0_run = Run(base_command, run_inputs, run_outputs, stdout, stderr)
    grep0_step = Step("grep0", grep0_run)

    # Step Grep1
    base_command = "grep"
    stdout = "occur1.txt"
    run_inputs = Inputs([RunInput("word", "string",
                         InputBinding(position=1), source="word1"),
                         RunInput("text_file", "File",
                         InputBinding(position=2), source="cat/contents")])
    run_outputs = Outputs([RunOutput("occur", "stdout")])
    grep1_run = Run(base_command, run_inputs, run_outputs, stdout, stderr)
    grep1_step = Step("grep1", grep1_run)

    # Step Tar
    base_command = "tar"
    stdout = "tar.txt"
    run_inputs = Inputs([RunInput("tarball_fname", "string",
                                  InputBinding(position=1, prefix="-cf")),
                         RunInput("file0", "File",
                                  InputBinding(position=2), source="grep0/occur"),
                         RunInput("file1", "File",
                                  InputBinding(position=3), source="grep1/occur")])
    run_outputs = Outputs([RunOutput("tarball", "File")])
    tar_run = Run(base_command, run_inputs, run_outputs, stdout, stderr)
    tar_step = Step("tar", tar_run)

    cgt_steps = Steps([cat_step, grep0_step, grep1_step, tar_step])
    cgt = CWL("catgreptar", cwl_inputs, cwl_outputs, cgt_steps)

    cgt_path = pathlib.Path("cat-grep-tar/")
    cgt_path.mkdir(exist_ok=True)
    cgt.dump_wf(cgt_path)
    cgt.dump_inputs(cgt_path)


if __name__ == "__main__":
    main()
