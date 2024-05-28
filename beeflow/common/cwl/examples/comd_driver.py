from beeflow.common.cwl.cwl import (CWL, CWLInput, RunInput, Inputs, CWLOutput,
                                    Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints)


def main():
    """Recreate the COMD workflow."""
    docker = DockerRequirement(docker_pull='lol')
    docker.dump()

    # CWLInputs
    cwl_inputs = Inputs([CWLInput('i', 'int', 20),
                         CWLInput('j', 'int', 10),
                         CWLInput('k', 'int', 10),
                         CWLInput('x', 'int', 10),
                         CWLInput('y', 'int', 10),
                         CWLInput('z', 'int', 10),
                         CWLInput('pot_dir', 'string', 10)
                         ])

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
    mpi = MPIRequirement(nodes=1, ntasks=27)
    container_path = '/usr/projects/beedev/mpi/comd-x86_64.tgz'
    docker = DockerRequirement(copy_container=container_path)
    hints = Hints(mpi_requirement=mpi, docker_requirement=docker)
    comd_run = Run(base_command, run_inputs, run_outputs, stdout)
    comd_step = Step('comd', comd_run, hints)
    comd_steps = Steps([comd_step])
    comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)
    print(comd)


if __name__ == "__main__":
    main()
