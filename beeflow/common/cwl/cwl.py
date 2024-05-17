"""Create and manage CWL files."""
from dataclasses import dataclass

# Number of spaces in a tab
# Define this just in case we ever want to change it in the future
TAB_SPACES = 2
TAB = " " * TAB_SPACES


@dataclass
class Header:
    """Represents a CWL header."""
    class_type: str = "CommmandLineTool"
    cwl_version: str = "v1.0"

    def __repr__(self):
        header = []
        header.append(f'class: {self.class_type}')
        header.append(f'cwlVersion: {self.cwl_version}')
        return '\n'.join(header)


@dataclass
class Input:
    """Represents a CWL input."""
    input_name: str
    input_type: str

    @property
    def input_type(self):
        """Define input type."""
        return self._input_type

    @input_type.setter
    def input_type(self, value: str):
        if value not in ('File', 'string', 'int'):
            raise NameError(f"{value} is an invalid input type must be either"
                            "File or string.")
        self._input_type = value

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        input_str = f'{TAB}{self.input_name}: {self.input_type}'
        return input_str


class Inputs:
    """Represents inputs for a workflow."""
    def __init__(self):
        self.inputs = {}

    def add_input(self, input_name, input_type):
        """Add an input to the workflow."""
        if input_name in self.inputs:
            raise NameError("Can't add input that overwrites existing input!")
        self.inputs[input_name] = Input(input_name, input_type)

    def remove_input(self, input_name):
        """Remove input from the workflow."""
        del self.inputs[input_name]


@dataclass
class Output:
    """Represents a CWL input."""
    output_name: str
    output_type: str
    output_source: str = None

    def __repr__(self):
        """Representation of an input.
           input_name: input_type
        """
        output = []
        output.append(f'{TAB}{self.output_name}:')
        output.append(self.output_type)
        if self.output_source is not None:
            output.append(self.output_source)
        out_str = f'{self.input_name}: {self.input_type}'
        return input_str


class Outputs:
    """Represents outputs for a workflow."""
    def __init__(self):
        self.outputs = []

    def add_output(self, output_name, output_type, k):
        """Add output to the workflow."""
        pass

    def remove_output(self):
        """Remove output from the workflow."""
        pass


class Steps:
    """Represents steps in a CWL file."""

class CWLFile:
    """Class represents a CWL file."""
    def __init__(self):
        # We currently represent a CWL file with a list of lines where each
        # line represents a piece of the file
        self.header = Header()
        self.inputs = Inputs()

    def add_step(self, step_name, base_command):
        """Add a step to the workflow."""
        pass
