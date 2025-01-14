"""Workflow front end for CWL generator."""
from dataclasses import dataclass

from beeflow.common.cwl.cwl import (CWL, CWLInput, CWLInputs, RunInput, Inputs, CWLOutput,
                                    Outputs, Run, RunOutput, Step, Steps,
                                    InputBinding, MPIRequirement, DockerRequirement, Hints)


@dataclass
class Input:
    """Represents CWL and Run inputs"""
    name: str
    type_: str
    default_value: str
    # The prefix or position of the argument
    # This can either be a prefix such as -f or --file
    # Or a position like 2 if the command is "foo <file>"
    prefix: str = None
    position: int = None

    def cwl_input(self):
        """Create a CWLInput from generic Input."""
        return CWLInput(self.name, self.type_, self.default_value)

    def run_input(self):
        """Create a RunInput from generic Input."""
        if self.prefix:
            run = RunInput(self.name, self.type_, InputBinding(prefix=self.prefix))
        elif self.position:
            run = RunInput(self.name, self.type_, InputBinding(position=self.position))
        return run


@dataclass
class Output:
    name: str
    type_: str
    source: str

    def cwl_output(self):
        """Create a RunOutput from generic Input."""
        return CWLOutput(self.name, self.type_, self.source)

    def run_output(self):
        """Create a RunOutput from generic Input."""
        return RunOutput(self.name, self.type_)
    

@dataclass
class MPI:
    nodes: int
    ntasks: int
        
    def requirement(self):
        return MPIRequirement(self.nodes, self.ntasks)


@dataclass
class Charliecloud:
    container: str

    def requirement(self):
        return DockerRequirement(copy_container = self.container)


@dataclass
class Task:
    """Represents a task."""
    name: str
    base_command: str
    stdout: str = None
    stderr: str = None
    inputs: list
    outputs: list
    hints: list = None

class Workflow:

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks
        self.generate_cwl()
            
    def generate_step(self, task):
        """Generates a Step object based off a Task object."""
        # Convert each input to a run input
        base_command = task.base_command
        run_inputs = Inputs([input_.run_input() for input_ in task.inputs])
        run_outputs = Outputs([output_.run_output() for output_ in task.outputs])
        stdout = task.stdout

        step_run = Run(base_command, run_inputs, run_outputs, stdout)
        step_hints = Hints([hint.requirement() for hint in task.hints])
        # print(step_hints)
        step_name = task.name

        # print(f'Step_name: {step_name} Step_run: {step_run} Step_hints: {step_hints}')
        step = Step(step_name, step_run, step_hints)
        return step

    def generate_cwl(self):
        """Generate a CWL object from a Workflow object."""
        cwl_inputs = []
        for task in self.tasks:
            cwl_inputs.extend([input_.cwl_input() for input_ in task.inputs])
        cwl_inputs = CWLInputs(cwl_inputs)

        cwl_outputs = []
        for task in self.tasks:
            cwl_outputs.extend([output_.cwl_output() for output_ in task.outputs])
        cwl_outputs = Outputs(cwl_outputs)

        cwl_steps = Steps([self.generate_step(task) for task in self.tasks])
        self.cwl = CWL(self.name, cwl_inputs, cwl_outputs, cwl_steps)

    def write(self, path=None):
        print(self.cwl.dump_wf())
