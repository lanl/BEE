"""COMD driver for CWL generator."""
import pathlib
from beeflow.common.cwl.workflow import (Task, Input, Output, MPI, Charliecloud,
                                         Workflow, Slurm, Script)


def main():
    """Recreate the COMD workflow."""
    # Specifies the comd task
    comd_task = Task(name="comd",
                     base_command="/CoMD/bin/CoMD-mpi -e",
                     stdout="comd.txt",
                     stderr="comd.err",
                     # list of Input objects
                     # The 2s and 40s are the actual value we want these to be
                     # this is how one sets input parameters. Prefix is just the
                     inputs=[Input("i", "int", 2, prefix="-i"),
                             Input("j", "int", 2, prefix="-j"),
                             Input("k", "int", 2, prefix="-k"),
                             Input("x", "int", 40, prefix="-x"),
                             Input("y", "int", 40, prefix="-y"),
                             Input("z", "int", 40, prefix="-z"),
                             Input("pot_dir", "string", "/CoMD/pots", prefix="--potDir")],
                     # List of Output objects.
                     # In this case we just have a file that represents stdout.
                     # The important part here is the source field that states
                     #   this output comes from this task
                     outputs=[Output("comd_stdout", "File", source="comd/comd_stdout")],
                     hints=[
                        Script(pre_script="comd_pre.sh"),
                        # Pass an sbatch script
                        Slurm(sbatch="run.sh"),
                     ])
    workflow = Workflow("comd", [comd_task])
    workflow.dump_wf("comd")
    workflow.dump_yaml("comd")

if __name__ == "__main__":
    main()
