"""
use_script.py

CWL generator to provide a specification to run a BEE workflow:

Purpose of the Workflow:
     Test the Slurm Requirement to use an existing batch script 
     and a step without inputs or base command in the python generator.

This generator creates directory, use-script, containing:

     use-script.cwl
     use-script.cwl
     batch.sh - contains the commands defined by RUN_SH

The workflow specification has one task, creating job:
    sbatch: runs batch.sh

Commands to create and run the workflow (assumes beeflow is running):
    python use_script.py
    cd use-script
    beeflow submit <wf-name> ./ ./use-script.cwl ./use-script.yml .

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
    """One step sumbit a script."""

    # Inputs and base command are not present
    sbatch = Task(name="sbatch",
               stdout="sbatch.out",
               stderr="sbatch.err",
               outputs=[Output('sbatch_stdout', 'stdout', source='sbatch/sbatch_stdout'),
                        Output('sbatch_stderr', 'stderr', source='sbatch/sbatch_stderr')],
               hints=[
                    Slurm(sbatch="batch.sh")])


    workflow = Workflow("use-script", [sbatch])
    workflow.dump_wf("use-script")
    workflow.dump_yaml("use-script")

    with open("use-script/batch.sh", "w") as f:
         f.write(RUN_SH)

   #Create blank file parser is looking for

if __name__ == "__main__":
    main()
