"""Example driver for comd."""
from beeflow.common.cwl.cwl import (CWL, CWLInput, RunInput, Inputs, CWLOutput,
                                    Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints)


def main():
    """Recreate the COMD workflow."""
    docker = DockerRequirement(docker_pull='lol')
    docker.dump()

    # CWLInputs
    cwl_inputs = Inputs([CWLInput('i', 'int'),
                         CWLInput('j', 'int'),
                         CWLInput('k', 'int'),
                         CWLInput('x', 'int'),
                         CWLInput('y', 'int'),
                         CWLInput('z', 'int'),
                         CWLInput('pot_dir', 'string')
                         ])

    # CWLOutputs
    cwl_outputs = Outputs([CWLOutput('comd_stdout', 'File', 'comd/comd_stdout')])

    # Step Run
    base_command = "'[/CoMD/bin/CoMD-mpi, '-e']'"
    stdout = 'comd_stdout.txt'
    run_inputs = Inputs([RunInput('i', 'int', InputBinding(prefix='-i'), 2),
                         RunInput('j', 'int', InputBinding(prefix='-j'), 2),
                         RunInput('k', 'int', InputBinding(prefix='-k'), 2),
                         RunInput('x', 'int', InputBinding(prefix='-x'), 40),
                         RunInput('y', 'int', InputBinding(prefix='-y'), 40),
                         RunInput('z', 'int', InputBinding(prefix='-z'), 40),
                         RunInput('pot_dir', 'string', InputBinding(prefix='--potDir'),
                                  '/CoMD/pots')])

    run_outputs = Outputs([RunOutput('comd_stdout', 'stdout')])
    mpi = MPIRequirement(nodes=4, ntasks=8)
    container_path = '/usr/projects/beedev/mpi/comd-x86_64.tgz'
    docker = DockerRequirement(copy_container=container_path)
    hints = Hints(mpi_requirement=mpi, docker_requirement=docker)
    comd_run = Run(base_command, run_inputs, run_outputs, stdout)
    comd_step = Step('comd', comd_run, hints)
    comd_steps = Steps([comd_step])
    comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)
    comd.dump()


if __name__ == "__main__":
    main()
