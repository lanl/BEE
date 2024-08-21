"""COMD driver for CWL generator."""
import pathlib
from beeflow.common.cwl.cwl import (CWL, CWLInput, CWLInputs, RunInput, Inputs, CWLOutput,
                                    Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints)


def main():
    """Recreate the COMD workflow."""
    # CWLInputs
    cwl_inputs = CWLInputs([CWLInput('i', 'int', value=2),
                            CWLInput('j', 'int', value=2),
                            CWLInput('k', 'int', value=2),
                            CWLInput('x', 'int', value=40),
                            CWLInput('y', 'int', value=40),
                            CWLInput('z', 'int', value=40),
                            CWLInput('pot_dir', 'string', value='/CoMD/pots')])

    # CWLOutputs
    cwl_outputs = Outputs([CWLOutput('comd_stdout', 'File', 'comd/comd_stdout')])

    # Step Run
    base_command = "'[/CoMD/bin/CoMD-mpi, '-e']'"
    stdout = 'comd_stdout.txt'
    run_inputs = Inputs([RunInput('i', 'int', InputBinding(prefix='-i')),
                         RunInput('j', 'int', InputBinding(prefix='-j')),
                         RunInput('k', 'int', InputBinding(prefix='-k')),
                         RunInput('x', 'int', InputBinding(prefix='-x')),
                         RunInput('y', 'int', InputBinding(prefix='-y')),
                         RunInput('z', 'int', InputBinding(prefix='-z')),
                         RunInput('pot_dir', 'string', InputBinding(prefix='--potDir'))])

    run_outputs = Outputs([RunOutput('comd_stdout', 'stdout')])
    mpi = MPIRequirement(nodes=4, ntasks=8)
    container_path = '/usr/projects/beedev/mpi/comd-x86_64.tgz'
    docker = DockerRequirement(copy_container=container_path)
    hints = Hints(mpi_requirement=mpi, docker_requirement=docker)
    comd_run = Run(base_command, run_inputs, run_outputs, stdout)
    comd_step = Step('comd', comd_run, hints)
    comd_steps = Steps([comd_step])
    comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)

    comd_path = pathlib.Path("comd/")
    comd_path.mkdir(exist_ok=True)
    comd.dump_wf(comd_path)
    comd.dump_inputs(comd_path)


if __name__ == "__main__":
    main()
