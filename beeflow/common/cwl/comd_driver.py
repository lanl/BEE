"""This is a docstring."""
from cwl import (CWL, CWLInput, RunInput, Inputs, CWLOutput, Outputs,
                 Run, RunOutput, Step, Steps, InputBinding)

# CWLInputs
cwl_inputs = Inputs([CWLInput('i', 'int', 20),
                 CWLInput('j', 'int', 10),
                 CWLInput('k', 'int', 10),
                 CWLInput('x', 'int', 10),
                 CWLInput('y', 'int', 10),
                 CWLInput('z', 'int', 10),
                 CWLInput('pot_dir', 'string', 10),
                 ])
# CWLOutputs
cwl_outputs = Outputs([CWLOutput('comd_stdout', 'File', 'comd/comd_stdout')])
# Step Run
base_command = '[/CoMD/bin/CoMD-mpi]'
stdout = 'comd_stdout.txt'
run_inputs = Inputs([RunInput('i', 'int', InputBinding(prefix='-i')),
                     RunInput('j', 'int', InputBinding(prefix='-j')),
                     RunInput('k', 'int', InputBinding(prefix='-k')),
                     RunInput('x', 'int', InputBinding(prefix='-x')),
                     RunInput('y', 'int', InputBinding(prefix='-y')),
                     RunInput('z', 'int', InputBinding(prefix='-z')),
                     RunInput('pot_dir', 'string',
                         InputBinding(prefix='--potDir'))])
run_outputs = Outputs([RunOutput('comd_stdout', 'stdout')])
hints = []
comd_run = Run(base_command, run_inputs, run_outputs, stdout, hints)
comd_step = Step('comd', comd_run, hints)
comd_steps = Steps([comd_step])
print(comd_steps)
comd = CWL('comd', cwl_inputs, cwl_outputs, comd_steps)
