"""COMD driver for CWL generator."""
import pathlib
from beeflow.common.cwl.workflow import Task, Input, Output, MPI, Charliecloud, Workflow, Slurm


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
                     # List of Output objects. In this case we just have a file that represents stdout.
                     # The important part here is the source field which states that this output comes from this task
                     outputs=[Output("comd_stdout", "File", source="comd/comd_stdout")],
                     hints=[
                        # The slurm requirement 
                        MPI(nodes=4, ntasks=8),
                        # Example of slurm options
                        #Slurm(account="standard", time_limit=60, partition="standard",
                        #      qos="debug", reservation="standard"),
                        Slurm(time_limit=500),
                        Charliecloud(docker_file="Dockerfile.comd-x86_64", container_name="comd-mpi")
                     ])
    workflow = Workflow("comd", [comd_task])
    workflow.write_wf("comd")
    workflow.write_yaml("comd")
    # workflow = Workflow("comd", [comd_task])
    # workflow.write(".")


if __name__ == "__main__":
    main()
