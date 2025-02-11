"""COMD driver for CWL generator."""
import pathlib
from beeflow.common.cwl.cwl import (CWL, CWLInput, CWLInputs, RunInput, Inputs, CWLOutput,
                                    CWLOutputs, Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints,
                                    RunInputs)

class Task:
    def __init__(self, name, inputs):
        self.name = name

class Input:
    def __init__(self, name, type, default, input_binding):
        self.name = name
        self.type = type
        self.default = default
        self.input_binding = input_binding

    def _generate_run_input(self):
        pass

    def _generate_cwl_input(self):
        pass

def main():
    """Recreate the COMD workflow."""
    # Example Input('x', type='int', default=2, input_binding='-x')),
    comd_task = Task("comd", 
                     Inputs(
                            Input('i', 'int', 2, '-i'),
                            Input('j', 'int', 2, '-j'),
                            Input('k', 'int', 2, '-k'),
                            Input('x', 'int', 2, '-x'),
                            Input('y', 'int', 40, '-y'),
                            Input('z', 'int', 40, '-z'),
                            Input('pot_dir', 'string', '/CoMD/post', '--potDir')
                           ), 
                     Outputs(),
                     Hints(
                            mpi_requirement=MPIRequirement(nodes=4, ntasks=8),
                            docker_requirement=DockerRequirement('/usr/projects/beedev/mpi/comd-x86_64.tgz')
                     )
                )
    Workflow(comd_task)
    # CWLInputs
    cwl_inputs = CWLInputs([CWLInput('i', 'int', value=2),
                            CWLInput('j', 'int', value=2),
                            CWLInput('k', 'int', value=2),
                            CWLInput('x', 'int', value=40),
                            CWLInput('y', 'int', value=40),
                            CWLInput('z', 'int', value=40),
                            CWLInput('pot_dir', 'string', value='/CoMD/pots')])

    # CWLOutputs
    cwl_outputs = CWLOutputs([CWLOutput('comd_stdout', 'File', 'comd/comd_stdout')])

    # Step Run
    base_command = "'[/CoMD/bin/CoMD-mpi, '-e']'"
    stdout = 'comd_stdout.txt'
    run_inputs = RunInputs([RunInput('i', 'int', InputBinding(prefix='-i')),
                          RunInput('j', 'int', InputBinding(prefix='-j')),
                          RunInput('k', 'int', InputBinding(prefix='-k')),
                          RunInput('x', 'int', InputBinding(prefix='-x')),
                          RunInput('y', 'int', InputBinding(prefix='-y')),
                          RunInput('z', 'int', InputBinding(prefix='-z')),
                          RunInput('pot_dir', 'string', InputBinding(prefix='--potDir'))])

    run_outputs = Outputs([RunOutput('comd_stdout', 'stdout')])
    container_path = 
    hints = Hints(mpi_requirement=MPIRequirement(nodes=4, ntasks=8),
                  docker_requirement=DockerRequirement(copy_container=container_path))
    comd_steps = Steps([Step('comd', Run(base_command, run_inputs, run_outputs, stdout), hints)])
    comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)

    comd_path = pathlib.Path("comd/")
    comd_path.mkdir(exist_ok=True)
    print(comd.dump_wf(comd_path))
    print(comd.dump_inputs(comd_path))


if __name__ == "__main__":
    main()
