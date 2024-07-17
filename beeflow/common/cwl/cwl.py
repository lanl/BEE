"""Create and manage CWL files."""
from dataclasses import dataclass
import yaml


@dataclass
class Header:
    """Represents a CWL header."""
    class_type: str = "Workflow"
    cwl_version: str = "v1.0"

    def dump(self):
        """Dump CWL header dictionary."""
        return {'class': self.class_type, 'cwlVersion': self.cwl_version}

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class Input:
    """The base input class. Used by CWLInput and RunInput.
        CWLInput has an input_default while RunInput has an inputBinding
        and RunInput has an inputBinding
    """
    input_name: str
    input_type: str

    # @property
    # def input_type(self):
    #     """Define input type."""
    #     return self._input_type

    # @input_type.setter
    # def input_type(self, value: str):
    #     if value not in ('File', 'string', 'int'):
    #         raise NameError(f"{value} is an invalid input type must be either"
    #                         "File or string.")
    #     self._input_type = value

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        input_yaml = {self.input_name: self.input_type}
        return input_yaml

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class CWLInput(Input):
    """Represents a CWL input as opposed to a Run input."""


@dataclass
class InputBinding:
    """Represents a CWL input binding."""
    prefix: str = None
    position: int = None

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        binding_yaml = {'inputBinding': {}}
        if self.position:
            binding_yaml['inputBinding']['position'] = self.position
        if self.prefix:
            binding_yaml['inputBinding']['prefix'] = self.prefix
        return binding_yaml

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class RunInput(Input):
    """Represents a Run input as opposed to a CWL input.

       InputBinding can either be:
            prefix: <-j> or empty {}
    """
    input_binding: InputBinding
    input_value: str

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        inputs_dumps = [{'type': self.input_type},
                        self.input_binding.dump()]
        inputs_dict = {}
        for dump in inputs_dumps:
            inputs_dict.update(dump)
        inputs_yaml = {self.input_name: inputs_dict}
        return inputs_yaml

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        return yaml.dump(self.dump(), sort_keys=False)


class Inputs:
    """Represents CWL or Run inputs for a workflow."""
    def __init__(self, inputs=None):
        self.inputs = inputs

    def dump(self):
        """Returns CWL input dict."""
        inputs_dumps = [i.dump() for i in self.inputs]
        inputs_dict = {}
        for d in inputs_dumps:
            inputs_dict.update(d)
        input_yaml = {'inputs': inputs_dict}
        return input_yaml

    def __add__(self, adder_inputs):
        new_inputs = self.inputs + adder_inputs.inputs
        return Inputs(new_inputs)

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class Output:
    """Represents a CWL input."""
    output_name: str
    output_type: str

    def dump(self):
        """Dump the output to a dictionary.
           output_name:
             type: output_type
        """
        output = {self.output_name: {'type': self.output_type}}
        return output

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)

@dataclass
class OutputBinding:
    """Represents a CWL input binding."""
    prefix: str = None
    position: int = None

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        binding_yaml = {'outputBinding': {}}
        if self.position:
            binding_yaml['outputBinding']['position'] = self.position
        if self.prefix:
            binding_yaml['outputBinding']['prefix'] = self.prefix
        return binding_yaml

    def __repr__(self):
        """Representation of an output.
           output_name: output_type
        """
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class RunOutput(Output):
    """Represents a Run output as opposed to a CWL output.

       InputBinding can either be:
            prefix: <-j>
            {}
    """
    output_binding: OutputBinding = None

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        if not self.output_binding:
            return super().dump()
        outputs_dumps = [{'type': self.output_type},
                        self.output_binding.dump()]
        outputs_dict = {}
        for dump in outputs_dumps:
            outputs_dict.update(dump)
        inputs_yaml = {self.output_name: outputs_dict}
        return inputs_yaml

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        return yaml.dump(self.dump(), sort_keys=False)



@dataclass
class CWLOutput(Output):
    """Represents a CWL input."""
    output_source: str = None

    def dump(self):
        """Dump the output to a dictionary.
           output_name:
             type: output_type
             outputSource: output_src/output_name
        """
        if self.output_source is not None:
            output = {self.output_name: {'type': self.output_type,
                      'outputSource': self.output_source}}
        else:
            output = {self.output_name: {'type': self.output_type}}
        return output

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


class Outputs:
    """Represents inputs for a workflow."""
    def __init__(self, outputs):
        self.outputs = outputs

    def dump(self):
        """Dumps workflow inputs to a dictionary."""
        outputs_dumps = [i.dump() for i in self.outputs]
        outputs_dict = {k: v for d in outputs_dumps for k, v in d.items()}
        output_yaml = {'outputs': outputs_dict}
        return output_yaml

    def __add__(self, adder_outputs):
        new_outputs = self.outputs + adder_outputs.outputs
        return Outputs(new_outputs)

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class DockerRequirement:
    """Defines docker requirement."""
    docker_pull: str = None
    docker_file: str = None
    copy_container: str = None
    use_container: str = None
    container_name: str = None
    force_type: str = None

    def dump(self):
        """Dumps docker requirement to a dictionary."""
        docker_dump = {'DockerRequirement': {}}
        if self.docker_pull:
            docker_dump['DockerRequirement']['dockerPull'] = self.docker_pull
        if self.docker_file:
            docker_dump['DockerRequirement']['dockerFile'] = self.docker_file
        if self.copy_container:
            docker_dump['DockerRequirement']['beeflow:copyContainer'] = self.copy_container
        if self.use_container:
            docker_dump['DockerRequirement']['beeflow:useContainer'] = self.use_container
        if self.container_name:
            docker_dump['DockerRequirement']['beeflow:containerName'] = self.container_name
        if self.force_type:
            docker_dump['DockerRequirement']['beeflow:force=Type'] = self.force_type
        return docker_dump

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class MPIRequirement:
    """Represents a beeflow custom MPI requirement."""
    nodes: int = None
    ntasks: int = None

    def dump(self):
        """Dumps MPI requirement to dictionary."""
        mpi_dump = {'beeflow:MPIRequirement': {}}
        if self.nodes:
            mpi_dump['beeflow:MPIRequirement']['nodes'] = self.nodes
        if self.ntasks:
            mpi_dump['beeflow:MPIRequirement']['ntasks'] = self.ntasks
        return mpi_dump

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class CheckpointRequirement:
    """Represents a beeflow checkpoint requirement."""
    file_path: str
    container_path: str
    file_regex: str
    restart_parameters: str
    num_tries: int
    enabled: bool = True

    def dump(self):
        """Dumps beeflow requirement to a dictionary."""
        req_name = 'beeflow:CheckpointRequirement'
        checkpoint_dump = {req_name: {}}
        checkpoint_dump[req_name]['enabled'] = self.enabled
        checkpoint_dump[req_name]['file_path'] = self.file_path
        checkpoint_dump[req_name]['container_path'] = self.container_path
        checkpoint_dump[req_name]['file_regex'] = self.file_regex
        checkpoint_dump[req_name]['restart_parameters'] = self.restart_parameters
        checkpoint_dump[req_name]['num_tries'] = self.enabled
        return req_name

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class ScriptRequirement:
    """Represents a beeflow custom pre/post script requirement."""
    pre_script: str = None
    post_script: str = None
    enabled: bool = True
    shell: str = "/bin/bash"

    def dump(self):
        """Dumps script requirement to a dcitionary."""
        key = 'beeflow:ScriptRequirement'
        script_dump = {key: {}}
        if self.pre_script:
            script_dump[key]['pre_script'] = self.pre_script
        if self.post_script:
            script_dump[key]['post_script'] = self.post_script
        script_dump[key]['enabled'] = self.enabled
        script_dump[key]['shell'] = self.shell
        return script_dump

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class Hints:
    """Holds all the hints for a CWL workflow."""
    mpi_requirement: MPIRequirement = None
    docker_requirement: DockerRequirement = None
    script_requirement: ScriptRequirement = None
    checkpoint_requirement: CheckpointRequirement = None

    def dump(self):
        """Dumps hints to a dictionary."""
        hints_dump = {'hints': {}}
        if self.mpi_requirement:
            hints_dump['hints'].update(self.mpi_requirement.dump())
        if self.docker_requirement:
            hints_dump['hints'].update(self.docker_requirement.dump())
        if self.script_requirement:
            hints_dump['hints'].update(self.script_requirement.dump())
        if self.checkpoint_requirement:
            hints_dump['hints'].update(self.checkpoint_requirement.dump())
        return hints_dump

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


class Run:
    """Represents a run section for a CWL workflow.
       Each task in a CWL workflow has a run section which can either be
       external to the main CWL file in its own CWL or be embedded directly
       into the main CWL file. For now, we're just embedding this directly
       into the main CWL file for ease of use, but might add an external option
       later.
    """
    def __init__(self, base_command, inputs, outputs, stdout):
        # This is implicit since we only support CommandLineTool steps atm
        self.run_class = 'CommandLineTool'
        self.base_command = base_command
        self.inputs = inputs
        self.outputs = outputs
        self.stdout = stdout

    def dump(self):
        """Dump run section into a dictionary."""
        run_dump = {'run': {}}
        run_dump['run']['class'] = self.run_class
        run_dump['run']['baseCommand'] = self.base_command
        run_dump['run']['stdout'] = self.stdout
        run_dump['run'].update(self.inputs.dump())
        run_dump['run'].update(self.outputs.dump())
        return run_dump

    def generate_in(self):
        """Generate the in section for a task. This maps to the inputs
           part of the run section which is then called in the step which holds
           that run section.
        """
        # Need to convert to a dictionary to get the keys
        # This is gross but the iterative solutions look grosser
        for i in self.inputs.inputs:
            print(i.input_value)
        #input_keys = list(list(self.inputs.dump().values())[0])
        in_ = {'in': {}}
        for i in self.inputs.inputs:
            in_['in'][i.input_name] = i.input_value
        return in_

    def generate_out(self):
        """Generate the out section for a task. This is the same as the in
           section, but it does require that the outputs are a list to produce
           the proper CWL.
        """
        out_keys = list(self.outputs.dump()['outputs'].keys())
        out_ = {'out': out_keys}
        return out_

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


class Step:
    """Represent a CWL step."""
    def __init__(self, step_name, run, hints):
        self.step_name = step_name
        self.run = run
        self.in_ = run.generate_in()
        self.out_ = run.generate_out()
        self.hints = hints

    def dump(self):
        """Dump step to a dictionary."""
        step_dump = {self.step_name: {}}
        step_dump[self.step_name].update(self.run.dump())
        step_dump[self.step_name].update(self.in_)
        step_dump[self.step_name].update(self.out_)
        step_dump[self.step_name].update(self.hints.dump())
        return step_dump

    def __repr__(self):
        return yaml.dump(self.dump(), default_flow_style=None, sort_keys=False)


class Steps:
    """Represent CWL steps."""
    def __init__(self, steps):
        self.steps = steps

    def dump(self):
        """Dump steps to a dictionary."""
        steps_dump = {'steps': {}}
        for step in self.steps:
            steps_dump['steps'].update(step.dump())
        return steps_dump

    def __repr__(self):
        return yaml.dump(self.dump(), default_flow_style=None, sort_keys=False)


class CWL:
    """Class represents a CWL workflow and all its components."""
    def __init__(self, cwl_name, inputs, outputs, steps):
        self.cwl_name = cwl_name
        self.header = Header()
        self.inputs = inputs
        self.outputs = outputs
        self.steps = steps

    def dump(self, path=None):
        """Dumps the workflow. If no path is specified print to stdout."""
        cwl_dump = {}
        cwl_dump.update(self.header.dump())
        cwl_dump.update(self.inputs.dump())
        cwl_dump.update(self.outputs.dump())
        cwl_dump.update(self.steps.dump())
        return cwl_dump

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)
