"""
write_script_baremetal.py

CWL generator to provide a specification to run a BEE workflow:

Purpose of the Workflow:
     Test the Slurm Requirement to accept a batch script written
     during the workflow and run it by subsequent task. The first step is run 
     on the front-end, thus "baremetal".

This generator creates directory, write-baremetal, containing:

     write-baremetal.cwl
     write-baremetal.yml
     batch.sh - contains the commands defined by RUN_SH

The workflow specification has two tasks, creating jobs:
    write: copies batch.sh to write-batch.sh (new file)
    sbatch: runs write-batch.sh

Commands to create and run the workflow (assumes beeflow is running):
    python write_script_baremetal.py
    cd write-baremetal
    beeflow submit <wf-name> ./ ./write-baremetal.cwl ./write-baremetal.yml .

"""

from pathlib import Path
from beeflow.common.cwl.workflow import Task, Input, Output, Workflow, Slurm, Workload

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

    # This step reads in batch.sh and writes it to batch_script.sh on the front-end
    write = Task(name="write",
               base_command="cat",
               stdout="batch_script.sh",
               stderr="write.err",
               inputs=[Input('input_file', 'File', "batch.sh", position=1)],
               outputs=[Output('write_stdout', 'stdout', source='write/write_stdout'),
                        Output('write_stderr', 'stderr', source='write/write_stderr')],
               hints=[Workload(mode="baremetal")])

    # Inputs are required for CWL dependency and base command not present since optional
    sbatch = Task(name="sbatch",
               stdout="sbatch.out",
               stderr="sbatch.err",
               inputs=[Input('text_file', 'File', "write/write_stdout", position=1)],
               outputs=[Output('sbatch_stdout', 'stdout', source='sbatch/sbatch_stdout'),
                        Output('sbatch_stderr', 'stderr', source='sbatch/sbatch_stderr')],
               hints=[
                    Slurm(sbatch="batch_script.sh")])


    workflow = Workflow("write-baremetal", [write, sbatch])
    #workflow = Workflow("write-baremetal", [write])
    workflow.dump_wf("write-baremetal")
    workflow.dump_yaml("write-baremetal")

    with open("write-baremetal/batch.sh", "w") as f:
         f.write(RUN_SH)

if __name__ == "__main__":
    main()
