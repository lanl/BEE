"""CWL workflow description parser.

Parses the contents of a CWL file and generates the graph representation of parsed workflows and
tools in the graph database. This parser supports a subset of the CWL v1.0 standard. It is
inspired by the CWL parser written by the CWL parser written by the SABER team at John Hopkins
University (see SABER project at https://github.com/aplbrain/saber).
"""
import configparser
import sys
import argparse
import json
import os
import yaml
import cwl_utils.parser_v1_2 as cwl_parser
from beeflow.common.config_driver import BeeConfig
from beeflow.common.wf_data import (InputParameter,
                                    OutputParameter,
                                    StepInput,
                                    StepOutput,
                                    Hint,
                                    Requirement)
from beeflow.common.wf_interface import WorkflowInterface

try:
    bc = BeeConfig()
    wfi = WorkflowInterface(user='neo4j', bolt_port=bc.userconfig.get('graphdb', 'bolt_port'),
                            db_hostname=bc.userconfig.get('graphdb', 'hostname'),
                            password=bc.userconfig.get('graphdb', 'dbpass'))
except KeyError:
    wfi = WorkflowInterface()
except configparser.NoSectionError:
    wfi = WorkflowInterface()

# Map CWL types to Python types
type_map = {
    'string': str,
    'int': int,
    'long': int,
    'float': float,
    'double': float,
    'File': str,
    'Directory': str,
}


class CwlParser:
    """Class for parsing CWL files."""

    def __init__(self):
        """Initialize a CWL parser."""
        self.cwl = None
        self.steps = []
        self.params = None

    def parse_workflow(self, cwl, job=None):
        """Parse a CWL Workflow file and load it into the graph database.

        :param cwl: the CWL file path
        :type cwl: str
        :param job: the input job file (YAML or JSON)
        :type job: str
        :rtype: tuple of (Workflow, list of Task)
        """
        self.cwl = cwl_parser.load_document(cwl)

        if self.cwl.class_ != "Workflow":
            raise ValueError(f"{os.path.basename(cwl)} class must be Workflow")

        if job:
            # Parse input job params into self.params
            self.parse_job(job)

        def resolve_input(input_, type_):
            """Resolve workflow input parameter from job file.

            :param input_: the workflow input name
            :type input_: str
            :param type_: the workflow input type
            :type type_: str
            :rtype: str or int or float
            """
            if not isinstance(self.params[input_], type_map[type_]):
                raise ValueError(f'Input/param types do not match: {input_}/{self.params[input_]}')
            return self.params[input_]

        workflow_name = os.path.basename(cwl).split(".")[0]
        workflow_inputs = {InputParameter(_shortname(input_.id), input_.type,
                                          resolve_input(_shortname(input_.id), input_.type))
                           for input_ in self.cwl.inputs}
        workflow_outputs = {OutputParameter(_shortname(output.id), output.type, None,
                                            _shortname(output.outputSource, True))
                            for output in self.cwl.outputs}
        workflow_hints = self.parse_requirements(self.cwl.hints, as_hints=True)
        workflow_requirements = self.parse_requirements(self.cwl.requirements)

        workflow = wfi.initialize_workflow(workflow_name, workflow_inputs, workflow_outputs,
                                           workflow_requirements, workflow_hints)
        tasks = [self.parse_step(step) for step in self.cwl.steps]

        return workflow, tasks

    def parse_step(self, step):
        """Parse a CWL step object.

        :param step: the CWL step object
        :type step: WorkflowStep
        :rtype: Task
        """
        step_cwl = cwl_parser.load_document(step.run)

        if step_cwl.class_ != "CommandLineTool":
            raise ValueError(f"{os.path.basename(step.run)} class must be CommandLineTool")

        step_name = os.path.basename(step_cwl.id).split(".")[0]
        step_command = step_cwl.baseCommand
        step_inputs = self.parse_step_inputs(step.in_, step_cwl.inputs)
        step_outputs = self.parse_step_outputs(step.out, step_cwl.outputs, step_cwl.stdout)
        step_requirements = self.parse_requirements(step.requirements)
        step_requirements.extend(self.parse_requirements(step_cwl.requirements))
        step_hints = self.parse_requirements(step.hints, as_hints=True)
        step_hints.extend(self.parse_requirements(step_cwl.hints, as_hints=True))
        step_stdout = step_cwl.stdout

        return wfi.add_task(step_name, base_command=step_command, inputs=step_inputs,
                            outputs=step_outputs, requirements=step_requirements, hints=step_hints,
                            stdout=step_stdout)

    def parse_job(self, job):
        """Parse a CWL input job file.

        :param job: the path of the input job file (YAML or JSON)
        :type job: str
        :rtype: dict
        """
        if job.endswith('.yml'):
            with open(job) as fp:
                self.params = yaml.full_load(fp)
        elif job.endswith('.json'):
            with open(job) as fp:
                self.params = json.load(fp)
        else:
            raise ValueError('Unsupported input job file extension')

        for k, v in self.params.items():
            if not isinstance(k, str):
                raise ValueError(f'Invalid input job key: {str(k)}')
            if not isinstance(v, (str, int, float)):
                raise ValueError(f'Invalid input job parameter type: {type(v)}')

    @staticmethod
    def parse_step_inputs(cwl_in, step_inputs):
        """Parse step inputs from CWL step input objects.

        :param cwl_in: the step inputs from the Workflow file
        :type cwl_in: list of WorkflowStepInput
        :param step_inputs: the step inputs from the CommandLineTool file
        :type step_inputs: list of CommandInputParameter
        :rtype: set of StepInput
        """
        source_map = {_shortname(input_.id).split("/")[-1]: _shortname(input_.source)
                      for input_ in cwl_in}

        inputs = set()
        for step_input in step_inputs:
            # If the input type is just a str, then the input is required
            # If it is a list containing 'null' and another type(s) then it is optional
            if _shortname(step_input.id) not in source_map.keys():
                if isinstance(step_input.type, str):
                    raise ValueError(f"required input {_shortname(step_input.id)} not satisfied")
                else:
                    continue

            if isinstance(step_input.type, str):
                input_type = step_input.type
            else:
                input_type = step_input.type[1]

            if step_input.inputBinding:
                inputs.add(StepInput(_shortname(step_input.id), input_type, None,
                                     source_map[_shortname(step_input.id)],
                                     step_input.inputBinding.prefix,
                                     step_input.inputBinding.position))
            else:
                inputs.add(StepInput(_shortname(step_input.id), input_type, None,
                                     source_map[_shortname(step_input.id)], None, None))

        return inputs

    @staticmethod
    def parse_step_outputs(cwl_out, step_outputs, stdout):
        """Parse step outputs from CWL step output objects.

        :param cwl_out: the step outputs from the Workflow file
        :type cwl_out: list of str
        :param step_outputs: the step outputs from the CommandLineTool file
        :type step_outputs: list of CommandOutputParameter
        :param stdout: name of file to which stdout should be redirected
        :type stdout: str or None
        :rtype: set of StepOutput
        """
        out_short = list(map(_shortname, cwl_out))
        short_id = out_short[0].split("/")[0]
        out_map = {short_id + "/" + _shortname(step_output.id): step_output
                   for step_output in step_outputs}

        outputs = set()
        for out in out_short:
            if out not in out_map.keys():
                raise ValueError(f"specified step output {out} not produced by CommandLineTool")

            output_type = out_map[out].type
            glob = None
            if output_type == "stdout":
                if not stdout:
                    raise ValueError((f"stdout capture required for step output {out} "
                                      "but not specified by CommandLineTool"))
                # Fill in glob with value of stdout
                glob = stdout
            else:
                if out_map[out].outputBinding:
                    glob = out_map[out].outputBinding.glob

            outputs.add(StepOutput(out, output_type, None, glob))

        return outputs

    @staticmethod
    def parse_requirements(requirements, as_hints=False):
        """Parse CWL hints/requirements.

        :param requirements: the CWL requirements
        :type requirements: list of ordereddict
        :param as_hints: parse as hints instead of requirements
        :type as_hints: bool
        :rtype: list of Hint or list of Requirement or None
        """
        reqs = []
        if not requirements:
            return reqs
        if as_hints:
            for req in requirements:
                reqs.append(Hint(req["class"], {k: v for k, v in req.items() if k != "class"}))
        else:
            for req in requirements:
                reqs.append(Requirement(req.class_, {k: v for k, v in vars(req).items()
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


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("wf_file", type=str, help="CWL workflow file")
    parser.add_argument("wf_inputs", type=str, help="Workflow job file")

    return parser.parse_args(args)


def main():
    parser = CwlParser()
    args = parse_args()
    workflow, tasks = parser.parse_workflow(args.wf_file, args.wf_inputs)


if __name__ == "__main__":
    sys.exit(main())