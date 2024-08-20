from beeflow.common.cwl.cwl import (CWL, CWLInput, RunInput, Inputs, CWLOutput,
                                    Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints)


def main():
    """Recreate the COMD workflow."""
    # CWLInputs
    cwl_inputs = Inputs([CWLInput('i', 'int'),
                         CWLInput('j', 'int'),
                         CWLInput('k', 'int'),
                         CWLInput('x', 'int'),
                         CWLInput('y', 'int'),
                         CWLInput('z', 'int'),
                         CWLInput('pot_dir', 'string')])

    # CWLOutputs
    cwl_outputs = Outputs([CWLOutput('comd_stdout', 'File', 'comd/comd_stdout')])

    # Step Run
    base_command = "'[/CoMD/bin/CoMD-mpi, '-e']'"
    stdout = 'comd_stdout.txt'
    run_inputs = Inputs([RunInput('i', 'int', InputBinding(prefix='-i'), value=2),
                         RunInput('j', 'int', InputBinding(prefix='-j'), value=2),
                         RunInput('k', 'int', InputBinding(prefix='-k'), value=2),
                         RunInput('x', 'int', InputBinding(prefix='-x'), value=40),
                         RunInput('y', 'int', InputBinding(prefix='-y'), value=40),
                         RunInput('z', 'int', InputBinding(prefix='-z'), value=40),
                         RunInput('pot_dir', 'string', InputBinding(prefix='--potDir'), value="/CoMD/pots")])

    run_outputs = Outputs([RunOutput('comd_stdout', 'stdout')])
    mpi = MPIRequirement(nodes=4, ntasks=8)
    container_path = '/usr/projects/beedev/mpi/comd-x86_64.tgz'
    docker = DockerRequirement(copy_container=container_path)
    hints = Hints(mpi_requirement=mpi, docker_requirement=docker)
    comd_run = Run(base_command, run_inputs, run_outputs, stdout)
    comd_step = Step('comd', comd_run, hints)
    comd_steps = Steps([comd_step])
    comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)
    comd.dump_wf()
    #comd.dump_inputs()


if __name__ == "__main__":
    main()
