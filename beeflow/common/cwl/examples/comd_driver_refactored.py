"""COMD driver for CWL generator."""
import pathlib
from beeflow.common.cwl.workflow import Task, Input, Output, MPI, Charliecloud, Workflow


def main():
    """Recreate the COMD workflow."""
    container_path = '/usr/projects/beedev/mpi/comd-x86_64.tgz'
    comd_task = Task(name="comd",
                     base_command="'[/CoMD/bin/CoMD-mpi, '-e']'",
                     stdout="comd_stdout",
                     stderr="comd_stderr",
                     inputs=[Input('i', 'int', 2, "-i"), Input('j', 'int', 2, "-i"),
                             Input('k', 'int', 2, "-k"), Input('x', 'int', 2, "-x"),
                             Input('y', 'int', 2, "-y"), Input('z', 'int', 2, "-z"),
                             Input('pot_dir', 'string', "/comd/pots", "--potDir")],
                     outputs=[Output('comd_stdout', 'File', 'comd/comd_stdout')],
                     hints=[
                        # Rename MPI to something like SchedulerOptions
                        MPI(nodes=4, ntasks=8),
                        Charliecloud(container=container_path)
                     ])
    workflow = Workflow("comd", [comd_task])
    workflow.write(".")


if __name__ == "__main__":
    main()
