"""
write_script.py

CWL generator to provide a specification to run a BEE workflow:

Purpose of the Workflow:
     Test the Slurm Requirement to accept a batch script written
     during the workflow and run it by subsequent task.

This generator creates directory, write-script, containing:

     write-script.cwl
     write-script.cwl
     batch.sh - contains the commands defined by RUN_SH
     write-batch.sh - blank file (required by CWL parser)

The workflow specification has two tasks, creating jobs:
    write: copies batch.sh to write-batch.sh
    sbatch: runs write-batch.sh

Commands to create and run the workflow (assumes beeflow is running):
    python write_script.py
    cd write-script
    beeflow submit <wf-name> ./ ./write-script.cwl ./write-script.yml .

"""

from pathlib import Path
from beeflow.common.cwl.workflow import Task, Input, Output, Workflow, Slurm

RUN_SH = """#!/bin/bash
#SBATCH --job-name=write_batch
#SBATCH --time=00:10:00
#SBATCH --output=write_batch.out
#SBATCH --error=write_batch.err
#SBATCH --nodes=1
#SBATCH --ntasks=1

echo "Job started on $(date)"
echo "Running on node(s): $SLURM_NODELIST"
echo "Job ID: $SLURM_JOB_ID"
echo "Job running at $PWD"
"""


def main():
    """Two step 1. Write a script. 2. Sumbit that script."""
#

    # This step reads in batch.sh and writes it to batch_script.sh
    write = Task(name="write",
               base_command="cat",
               stdout="batch_script.sh",
               stderr="write.err",
               inputs=[Input('input_file', 'File', "batch.sh", position=1)],
               outputs=[Output('write_stdout', 'stdout', source='write/write_stdout'),
                        Output('write_stderr', 'stderr', source='write/write_stderr')])

    # Inputs and base command are not used for the following step
    sbatch = Task(name="sbatch",
               base_command="cat",
               stdout="sbatch.out",
               stderr="sbatch.err",
               inputs=[Input('text_file', 'File', "write/write_stdout", position=1)],
               outputs=[Output('sbatch_stdout', 'stdout', source='sbatch/sbatch_stdout'),
                        Output('sbatch_stderr', 'stderr', source='sbatch/sbatch_stderr')],
               hints=[
                    Slurm(sbatch="batch_script.sh")])


    workflow = Workflow("write-script", [write, sbatch])
    #workflow = Workflow("write-script", [write])
    workflow.dump_wf("write-script")
    workflow.dump_yaml("write-script")

    with open("write-script/batch.sh", "w") as f:
         f.write(RUN_SH)

   #Create blank file parser is looking for
    path = Path("write-script/batch_script.sh")
    path.touch()

if __name__ == "__main__":
    main()
