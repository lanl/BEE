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
        """Return CWL header as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class Input:
    """The base input class. Used by CWLInput and RunInput.

    CWLInput has an input_default while RunInput has an inputBinding
    and RunInput has an inputBinding
    """

    input_name: str
    input_type: str

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

    value: str


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
    # For now source will just be a string but might make it a type later
    source: str = None

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
        """Initialize inputs."""
        self.inputs = inputs

    def dump(self):
        """Return CWL input dict."""
        inputs_dumps = [i.dump() for i in self.inputs]
        inputs_dict = {}
        for input_dump in inputs_dumps:
            inputs_dict.update(input_dump)
        input_yaml = {'inputs': inputs_dict}
        return input_yaml

    def __add__(self, adder_inputs):
        """Add inputs."""
        new_inputs = self.inputs + adder_inputs.inputs
        return Inputs(new_inputs)

    def __repr__(self):
        """Return Inputs as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


class CWLInputs(Inputs):
    """CWLInputs is different just so we can generate the YAML file."""

    def generate_yaml_inputs(self):
        """Return a dictionary that will be used to create job yaml file."""
        yaml_inputs = {}
        for i in self.inputs:
            yaml_inputs[i.input_name] = i.value
        return yaml_inputs


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
        """Return Output as a yaml string."""
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
        """Return CWLOutput as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


class Outputs:
    """Represents outputs for a workflow."""

    def __init__(self, outputs):
        """Initialize outputs."""
        self.outputs = outputs

    def dump(self):
        """Dump workflow inputs to a dictionary."""
        outputs_dumps = [i.dump() for i in self.outputs]
        outputs_dict = {k: v for d in outputs_dumps for k, v in d.items()}
        output_yaml = {'outputs': outputs_dict}
        return output_yaml

    def __add__(self, adder_outputs):
        """Add outputs."""
        new_outputs = self.outputs + adder_outputs.outputs
        return Outputs(new_outputs)

    def __repr__(self):
        """Return Outputs as a yaml string."""
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
        """Dump docker requirement to a dictionary."""
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
        """Return DockerRequirement as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class MPIRequirement:
    """Represents a beeflow custom MPI requirement."""

    nodes: int = None
    ntasks: int = None

    def dump(self):
        """Dump MPI requirement to dictionary."""
        mpi_dump = {'beeflow:MPIRequirement': {}}
        if self.nodes:
            mpi_dump['beeflow:MPIRequirement']['nodes'] = self.nodes
        if self.ntasks:
            mpi_dump['beeflow:MPIRequirement']['ntasks'] = self.ntasks
        return mpi_dump

    def __repr__(self):
        """Return MPIRequirement as a yaml string."""
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
        """Dump beeflow requirement to a dictionary."""
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
        """Return CheckpointRequirement as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class ScriptRequirement:
    """Represents a beeflow custom pre/post script requirement."""

    pre_script: str = None
    post_script: str = None
    enabled: bool = True
    shell: str = "/bin/bash"

    def dump(self):
        """Dump script requirement to a dcitionary."""
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
        """Return ScriptRequirement as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


@dataclass
class Hints:
    """Holds all the hints for a CWL workflow."""

    mpi_requirement: MPIRequirement = None
    docker_requirement: DockerRequirement = None
    script_requirement: ScriptRequirement = None
    checkpoint_requirement: CheckpointRequirement = None

    def dump(self):
        """Dump hints to a dictionary."""
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
        """Return Hint as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


class Run:
    """Represents a run section for a CWL workflow.

    Each task in a CWL workflow has a run section which can either be
    external to the main CWL file in its own CWL or be embedded directly
    into the main CWL file. For now, we're just embedding this directly
    into the main CWL file for ease of use, but might add an external option
    later.
    """

    def __init__(self, base_command, inputs, outputs, stdout, stderr=None):
        """Initialize Run."""
        # This is implicit since we only support CommandLineTool steps atm
        self.run_class = 'CommandLineTool'
        self.base_command = base_command
        self.inputs = inputs
        self.outputs = outputs
        self.stdout = stdout
        self.stderr = stderr

    def dump(self):
        """Dump run section into a dictionary."""
        run_dump = {'run': {}}
        run_dump['run']['class'] = self.run_class
        run_dump['run']['baseCommand'] = self.base_command
        run_dump['run']['stdout'] = self.stdout
        if self.stderr:
            run_dump['run']['stderr'] = self.stderr
        run_dump['run'].update(self.inputs.dump())
        run_dump['run'].update(self.outputs.dump())
        return run_dump

    def generate_in(self):
        """Generate the in section for a task as well as the YAML for a particular step.

        This maps to the inputs part of the run section which is then
        called in the step which holds that run section.
        """
        in_ = {'in': {}}
        for i in self.inputs.inputs:
            if i.source:
                in_['in'][i.input_name] = i.source
            else:
                in_['in'][i.input_name] = i.input_name
        return in_

    def generate_out(self):
        """Generate the out section for a task.

        This is the same as the in section, but it does require that
        the outputs are a list to produce the proper CWL.
        """
        out_keys = list(self.outputs.dump()['outputs'].keys())
        out_ = {'out': out_keys}
        return out_

    def __repr__(self):
        """Return Run as a yaml string."""
        return yaml.dump(self.dump(), sort_keys=False)


class Step:
    """Represent a CWL step."""

    def __init__(self, step_name, run, hints=None):
        """Initialize CWL step."""
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
        if self.hints:
            step_dump[self.step_name].update(self.hints.dump())
        return step_dump

    def __repr__(self):
        """Return CWL step as a string."""
        return yaml.dump(self.dump(), default_flow_style=None, sort_keys=False)


class Steps:
    """Represent CWL steps."""

    def __init__(self, steps):
        """Initialize the CWL step."""
        self.steps = steps

    def dump(self):
        """Dump steps to a dictionary."""
        steps_dump = {'steps': {}}
        for step in self.steps:
            steps_dump['steps'].update(step.dump())
        return steps_dump

    def __repr__(self):
        """Dump the CWL steps."""
        return yaml.dump(self.dump(), default_flow_style=None, sort_keys=False)


class CWL:
    """Class represents a CWL workflow and all its components."""

    def __init__(self, cwl_name, inputs, outputs, steps):
        """Initialize the CWL."""
        self.cwl_name = cwl_name
        self.header = Header()
        self.inputs = inputs
        self.outputs = outputs
        self.steps = steps

    def dump_wf(self, path=None):
        """Dump the workflow. If no path is specified print to stdout."""
        cwl_dump = {}
        cwl_dump.update(self.header.dump())
        cwl_dump.update(self.inputs.dump())
        cwl_dump.update(self.outputs.dump())
        cwl_dump.update(self.steps.dump())
        wf_contents = yaml.dump(cwl_dump, sort_keys=False)
        if path:
            with open(f"{path}/{self.cwl_name}.cwl", "w", encoding="utf-8") as wf_file:
                print(wf_contents, file=wf_file)
        return wf_contents

    def dump_inputs(self, path=None):
        """Dump YAML inputs."""
        yaml_contents = yaml.dump(self.inputs.generate_yaml_inputs(),
                                  sort_keys=False)
        if path:
            with open(f"{path}/{self.cwl_name}.yml", "w", encoding="utf-8") as yaml_file:
                print(yaml_contents, file=yaml_file)
        return yaml_contents

    def __repr__(self):
        """Return CWL file as a string."""
        return yaml.dump(self.dump_wf(), sort_keys=False)
