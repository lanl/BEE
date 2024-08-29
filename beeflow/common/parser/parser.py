"""CWL workflow description parser.

Parses the contents of a CWL file and generates the graph representation of parsed workflows and
tools in the graph database. This parser supports a subset of the CWL v1.0 standard. It is
inspired by the CWL parser written by the CWL parser written by the SABER team at John Hopkins
University (see SABER project at https://github.com/aplbrain/saber).
"""
import sys
import argparse
import json
import os
import traceback
import yaml
import cwl_utils.parser.cwl_v1_2 as cwl_parser
from schema_salad.exceptions import ValidationException  # noqa (pylama can't find the exception)

from beeflow.common.wf_data import (Workflow,
                                    Task,
                                    InputParameter,
                                    OutputParameter,
                                    StepInput,
                                    StepOutput,
                                    Hint,
                                    Requirement,
                                    generate_workflow_id)

# Map CWL types to Python types
type_map = {
    "string": str,
    "int": int,
    "long": int,
    "float": float,
    "double": float,
    "File": str,
    "Directory": str,
}


class CwlParseError(Exception):
    """Parser error class."""

    def __init__(self, *args):
        """Create a parser error."""
        self.args = args


class CwlParser:
    """Class for parsing CWL files."""

    def __init__(self):
        """Initialize the CWL parser interface.

        Sets the workflow interface for communication with the graph database.
        """
        self.cwl = None
        self.path = None
        self.steps = []
        self.params = None

    def parse_workflow(self, workflow_id, cwl_path, job=None):
        """Parse a CWL Workflow file and load it into the graph database.

        Returns an instance of the WorkflowInterface.

        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param cwl_path: the CWL file path
        :type cwl_path: str
        :param job: the input job file (YAML or JSON)
        :type job: str
        :rtype: WorkflowInterface
        """
        self.path = cwl_path
        try:
            self.cwl = cwl_parser.load_document(cwl_path)
        except ValidationException as err:
            traceback.print_exc()
            raise CwlParseError(*err.args) from None

        if self.cwl.class_ != "Workflow":
            raise CwlParseError(f"{os.path.basename(cwl_path)} class must be Workflow")

        if job:
            # Parse input job params into self.params
            self.parse_job(job)
        else:
            self.params = {}

        def resolve_input(input_, type_):
            """Resolve workflow input parameter from job file.

            :param input_: the workflow input name
            :type input_: WorkflowInputParameter
            :param type_: the workflow input type
            :type type_: str
            :rtype: (Workflow, list of Task)
            """
            # Use parsed input parameter for input value if it exists
            input_id = _shortname(input_.id)
            value = self.params[input_id] if input_id in self.params else input_.default
            if value is None:
                raise CwlParseError(f"input {input_id} is missing from workflow job file")
            if not isinstance(value, type_map[type_]):
                raise CwlParseError("Input/param types do not match: "
                                    f"{input_id}/{value}")
            return value

        workflow_name = os.path.basename(cwl_path).split(".")[0]
        workflow_inputs = {InputParameter(_shortname(input_.id), input_.type,
                                          resolve_input(input_, input_.type))
                           for input_ in self.cwl.inputs}
        workflow_outputs = {OutputParameter(_shortname(output.id), output.type, None,
                                            _shortname(output.outputSource, True))
                            for output in self.cwl.outputs}
        workflow_hints = self.parse_requirements(self.cwl.hints, as_hints=True)
        workflow_requirements = self.parse_requirements(self.cwl.requirements)

        workflow = Workflow(workflow_name, workflow_hints, workflow_requirements, workflow_inputs,
                            workflow_outputs, workflow_id)
        tasks = [self.parse_step(step, workflow_id) for step in self.cwl.steps]

        return workflow, tasks

    def parse_step(self, step, workflow_id):
        """Parse a CWL step object.

        Calling this to parse a CommandLineTool file without a corresponding
        Workflow file will fail.

        :param step: the CWL step object
        :type step: WorkflowStep
        :param workflow_id: the workflow ID
        :type workflow_id: str
        :rtype: Task
        """
        # Parse CWL file specified by run field, else parse run field as inline CommandLineTool
        if isinstance(step.run, str):
            step_run = f"{os.path.dirname(step.id)}/{step.run}"
            step_cwl = cwl_parser.load_document(step_run)
            step_id = os.path.basename(step_cwl.id).split(".")[0]
        else:
            step_cwl = step.run
            step_id = _shortname(step.id)
            # step_input.id needs to have its step.id prefix stripped
            for step_input in step_cwl.inputs:
                step_shortname = _shortname(step_input.id)
                step_input.id = step_input.id.replace(step_shortname,
                                                      step_shortname.split("/")[-1])

        if step_cwl.class_ != "CommandLineTool":
            raise CwlParseError(f"Step {step.id} class must be CommandLineTool")

        step_name = os.path.basename(step_id).split(".")[0]
        step_command = step_cwl.baseCommand
        step_inputs = self.parse_step_inputs(step.in_, step_cwl.inputs)
        step_outputs = self.parse_step_outputs(step.out, step_cwl.outputs, step_cwl.stdout,
                                               step_cwl.stderr)
        step_requirements = self.parse_requirements(step.requirements)
        step_requirements.extend(self.parse_requirements(step_cwl.requirements))
        step_hints = self.parse_requirements(step.hints, as_hints=True)
        step_hints.extend(self.parse_requirements(step_cwl.hints, as_hints=True))
        step_stdout = step_cwl.stdout
        step_stderr = step_cwl.stderr

        return Task(step_name, step_command, step_hints, step_requirements, step_inputs,
                    step_outputs, step_stdout, step_stderr, workflow_id)

    def parse_job(self, job):
        """Parse a CWL input job file.

        Input parameters are stored in the params attribute.

        :param job: the path of the input job file (YAML or JSON)
        :type job: str
        """
        if job.endswith(".yml") or job.endswith(".yaml"):
            with open(job, encoding="utf-8") as fp:
                self.params = yaml.full_load(fp)
        elif job.endswith(".json"):
            with open(job, encoding="utf-8") as fp:
                self.params = json.load(fp)
        else:
            raise CwlParseError("Unsupported input job file extension (only .yml "
                                "and .json supported)")

        for k, v in self.params.items():
            if not isinstance(k, str):
                raise CwlParseError(f"Invalid input job key: {str(k)}")
            if not isinstance(v, (str, int, float)):
                raise CwlParseError(f"Invalid input job parameter type: {type(v)}")

    @staticmethod
    def parse_step_inputs(cwl_in, step_inputs):
        """Parse step inputs from CWL step input objects.

        :param cwl_in: the step inputs from the Workflow file
        :type cwl_in: list of WorkflowStepInput
        :param step_inputs: the step inputs from the CommandLineTool file
        :type step_inputs: list of CommandInputParameter
        :rtype: list of StepInput
        """
        source_map = {_shortname(input_.id).split("/")[-1]: _shortname(input_.source)
                      for input_ in cwl_in}

        inputs = []
        for step_input in step_inputs:
            # If the input type is str, then the input is required
            # If it is a list containing 'null' and another type(s) then it is optional
            # If the input is not in the source_map but has a default value then it will
            # be set by the GDB later
            if _shortname(step_input.id) not in source_map.keys():
                if isinstance(step_input.type, str) and step_input.default is None:
                    raise CwlParseError(f"required input {_shortname(step_input.id)} "
                                        "not satisfied")
                continue

            if isinstance(step_input.type, str):
                input_type = step_input.type
            else:
                input_type = step_input.type[1]

            if step_input.inputBinding:
                inputs.append(StepInput(_shortname(step_input.id), input_type, None,
                                        step_input.default, source_map[_shortname(step_input.id)],
                                        step_input.inputBinding.prefix,
                                        step_input.inputBinding.position,
                                        step_input.inputBinding.valueFrom))
            else:
                inputs.append(StepInput(_shortname(step_input.id), input_type, None,
                                        step_input.default, source_map[_shortname(step_input.id)],
                                        None, None))

        return inputs

    @staticmethod
    def parse_step_outputs(cwl_out, step_outputs, stdout, stderr):
        """Parse step outputs from CWL step output objects.

        :param cwl_out: the step outputs from the Workflow file
        :type cwl_out: list of str
        :param step_outputs: the step outputs from the CommandLineTool file
        :type step_outputs: list of CommandOutputParameter
        :param stdout: name of file to which stdout should be redirected
        :type stdout: str or None
        :param stderr: name of file to which stderr should be redirected
        :type stderr: str or None
        :rtype: list of StepOutput
        """
        if not cwl_out:
            return []

        out_short = list(map(_shortname, cwl_out))
        short_id = out_short[0].split("/")[0]
        # Inline step outputs already have short_id+"/" prepended
        out_map = {(_shortname(step_output.id)
                   if _shortname(step_output.id).startswith(short_id + "/") else
                   short_id + "/" + _shortname(step_output.id)): step_output
                   for step_output in step_outputs}

        outputs = []
        for out in out_short:
            if out not in out_map.keys():
                raise CwlParseError(f"specified step output {out} not produced by CommandLineTool")

            output_type = out_map[out].type
            glob = None
            if output_type == "stdout":
                if not stdout:
                    raise CwlParseError(f"stdout capture required for step output {out} "
                                        "but not specified by CommandLineTool")
                # Fill in glob with value of stdout
                glob = stdout
            elif output_type == "stderr":
                if not stderr:
                    raise ValueError((f"stderr capture required for step output {out} "
                                      "but not specified by CommandLineTool"))
                # Fill in glob with value of stderr
                glob = stderr
            else:
                if out_map[out].outputBinding:
                    glob = out_map[out].outputBinding.glob

            outputs.append(StepOutput(out, output_type, None, glob))

        return outputs

    def _read_requirement_file(self, key, items):
        """Read in a requirement file and replace it in the parsed items."""
        base_path = os.path.dirname(self.path)
        fname = items[key]
        path = os.path.join(base_path, fname)
        try:
            with open(path, encoding='utf-8') as fp:
                items[key] = fp.read()
        except FileNotFoundError:
            msg = f'Could not find a file for {key}: {fname}'
            raise CwlParseError(msg) from None
        if key in {'pre_script', 'post_script'}:
            self._validate_prepost_shell_env(key, items, fname)

    def _validate_prepost_shell_env(self, key, items, fname):
        """Validate defined shell interpreters.

        :param fname: name of pre/post script file
        :type fname: str
        """
        env_decl = items[key].splitlines()
        # Need to remove whitespaces/newlines from list
        env_decl = [x for x in env_decl if x.strip()]
        # Check for shebang line in pre/post scripts
        if not env_decl[0].startswith("#!"):
            msg = f'No shebang line found in {fname}'
            raise CwlParseError(msg) from None
        # Now check for matching shell and shebang line values
        shell_val = '#!' + items['shell']
        shebang_val = env_decl[0]
        if shell_val != shebang_val:
            msg = f'CWL file shell {shell_val} does not match {fname} shell {shebang_val}'
            raise CwlParseError(msg) from None
        # Remove shebang lines from scripts
        rm_line = env_decl[1:]
        # List to string format
        rm_line = "\n".join(rm_line)
        items.update({key: rm_line})

    def parse_requirements(self, requirements, as_hints=False):
        """Parse CWL hints/requirements.

        :param requirements: the CWL requirements
        :type requirements: list of ordereddict or any cwl_utils Requirement class
        :param as_hints: parse as hints instead of requirements
        :type as_hints: bool
        :rtype: list of Hint or list of Requirement or None
        """
        reqs = []
        if not requirements:
            return reqs
        if as_hints:
            for req in requirements:
                items = {}
                for k, v in req.items():
                    if k != 'class':
                        if isinstance(v, (int, float)):
                            items[k] = v
                        else:
                            items[k] = str(v)
                # Load in the dockerfile at parse time
                if 'dockerFile' in items:
                    self._read_requirement_file('dockerFile', items)
                # Load in pre/post scripts and make sure shell option is defined in cwl file
                if 'pre_script' in items and items['enabled']:
                    if 'shell' in items:
                        self._read_requirement_file('pre_script', items)
                    else:
                        msg = f'pre script enabled but shell option undefined in cwl file.' #noqa
                        raise CwlParseError(msg) from None
                if 'post_script' in items and items['enabled']:
                    if 'shell' in items:
                        self._read_requirement_file('post_script', items)
                    else:
                        msg = f'post script enabled but shell option undefined in cwl file.' #noqa
                        raise CwlParseError(msg) from None
                if 'beeflow:bindMounts' in items:
                    self._read_requirement_file('beeflow:bindMounts', items)
                reqs.append(Hint(req['class'], items))
        else:
            for req in requirements:
                reqs.append(Requirement(req.class_, {k: str(v) for k, v in vars(req).items()
                                                     if k not in ("extension_fields",
                                                                  "loadingOptions", "class_")
                                                     and v is not None}))
        return reqs


def _shortname(uri, output_source=False):
    """Shorten a CWL object URI.

    e.g., file:///path/to/file#step/name -> step/name,
    or file:///path/to/file#output/output/source -> output/source if outputSource is True

    :param uri: a CWL object URI
    :type uri: str
    :param output_source: true if URI is for an outputSource object, else false
    :type output_source: bool
    """
    if output_source:
        output = uri.split("#")[-1]
        return "/".join(output.split("/")[1:])

    return uri.split("#")[-1]


def parse_args(args=None):
    """Parse arguments."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("wf_file", type=str, help="CWL workflow file")
    parser.add_argument("-i", "--inputs", type=str, help="Workflow job inputs file",
                        required=False)

    return parser.parse_args(args)


def main():
    """Run the parser on a CWL Workflow and job file directly."""
    wf_id = generate_workflow_id()
    parser = CwlParser()
    args = parse_args()
    workflow, tasks = parser.parse_workflow(wf_id, args.wf_file, args.inputs)
    print("Parsed workflow:")
    print(workflow)

    print("Parsed tasks:")
    print(tasks)


if __name__ == "__main__":
    sys.exit(main())
