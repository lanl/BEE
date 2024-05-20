"""Create and manage CWL files."""
from dataclasses import dataclass, field
from typing import List
import yaml

@dataclass
class Header:
    """Represents a CWL header."""
    class_type: str = "Workflow"
    cwl_version: str = "v1.0"

    def dump(self):
        return {'class':self.class_type, 'cwlVersion':self.cwl_version}

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

    #@property
    #def input_type(self):
    #    """Define input type."""
    #    return self._input_type

    #@input_type.setter
    #def input_type(self, value: str):
    #    if value not in ('File', 'string', 'int'):
    #        raise NameError(f"{value} is an invalid input type must be either"
    #                        "File or string.")
    #    self._input_type = value

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        input_yaml = {self.input_name:self.input_type}
        return input_yaml

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        return yaml.dump(self.dump(), sort_keys=False)

@dataclass
class CWLInput(Input):
    """Represents a CWL input as opposed to a Run input."""
    input_default: str = None

@dataclass 
class InputBinding:
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
            prefix: <-j>
            {}
    """
    input_binding: InputBinding

    def dump(self):
        """Dump returns dictionary that will be used by pyyaml dump."""
        inputs_dumps = [{'type':self.input_type}, 
                       self.input_binding.dump()]
        inputs_dict = {}
        for d in inputs_dumps:
            inputs_dict.update(d)
        inputs_yaml = {self.input_name:inputs_dict}
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
        inputs_dumps = [i.dump() for i in self.inputs]
        inputs_dict = {}
        for d in inputs_dumps:
            inputs_dict.update(d)
        input_yaml = {'inputs': inputs_dict}
        return input_yaml

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
        output = {self.output_name:{'type':self.output_type}}
        return output

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)

@dataclass 
class RunOutput(Output):
    pass

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
            output = {self.output_name:{'type':self.output_type,
                      'outputSource':self.output_source}}
        else:
            output = {self.output_name:{'type':self.output_type}}
        return output

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)

class Outputs:
    """Represents inputs for a workflow."""
    def __init__(self, outputs):
        self.outputs = outputs

    def dump(self):
        outputs_dumps = [i.dump() for i in self.outputs]
        # Need to ensure this uses correct order
        outputs_dict = {k:v for d in outputs_dumps for k, v in d.items()}
        output_yaml = {'outputs': outputs_dict}
        return output_yaml

    def __repr__(self):
        return yaml.dump(self.dump(), sort_keys=False)


class Hint:
    def __init__(self):
        pass

class Hints:
    def __init__(self):
        pass

class Run:
    def __init__(self, base_command, inputs, outputs, stdout, hints):
        # This is implicit since we only support CommandLineTool steps atm
        self.run_class = 'CommandLineTool'
        self.base_command  = base_command
        self.inputs = inputs
        self.outputs = outputs
        self.stdout = stdout

    def dump(self):
        run_dump = {'run': {}}
        run_dump['run']['class'] = self.run_class
        run_dump['run']['baseCommand'] = self.base_command
        run_dump['run']['stdout'] = self.stdout
        run_dump['run'].update(self.inputs.dump())
        run_dump['run'].update(self.outputs.dump())
        #run_dump['hints'] = self.hints.dump()
        return run_dump

    def generate_in(self):
        # Need to convert to a dictionary to get the keys
        # This is gross but the iterative solutions look grosser
        input_keys = list(list(self.inputs.dump().values())[0])
        in_ = {'in': {}}
        for i in input_keys:
            in_['in'][i] = i
        #in_ = yaml.dump(in_, sort_keys=False)
        return in_
    
    def generate_out(self):
        out_keys = list(list(self.outputs.dump().values())[0])
        if len(out_keys) == 1:
            out_ = f'[{out_keys[0]}]'
            out_ = {'out': [out_keys[0]]}
        else:
            out_ = '[' + ', '.join(out_keys[:-1]) + ', ' + out_keys[-1] + ']'
        #out_ = yaml.dump(out_, sort_keys=False)
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
        step_dump = {self.step_name: {}}
        step_dump[self.step_name].update(self.run.dump())
        #step_dump[self.step_name].update(self.in_)
        #step_dump[self.step_name].update(self.out_)
        return step_dump

    def __repr__(self):
        return yaml.dump(self.dump(), default_flow_style=True, sort_keys=False)

class Steps:
    """Represent CWL steps."""
    def __init__(self, steps):
        self.steps = steps

    def dump(self):
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
        print(self.header)
        print(self.inputs)
        print(self.outputs)
