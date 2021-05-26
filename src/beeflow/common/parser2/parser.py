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

        def resolve_inputs(wf_inputs):
            rv = {}
            for k, v in wf_inputs.items():
                print(f'inputs k: {k}   v: {v}')
                print(f'type(v):   {type_map[v]}')
                print(f'params[{k}]: {self.params[k]}')
                print(f'type(params[{k}]): {type(self.params[k])}')
                if not isinstance(self.params[k], type_map[v]):
                    raise ValueError(f'Types of input/param do not match: {v}/{self.params[k]}')
                rv[k] = self.params[k]
            return rv

        workflow_name = os.path.basename(cwl).split(".")[0]
        # Steven had tuples, I changed to dict to mirror output of parse_job
        #workflow_inputs = {_shortname(input_.id): input_.type for input_ in self.cwl.inputs}
        workflow_inputs = {_shortname(input_.id) for input_ in self.cwl.inputs}
        #resolved_inputs = resolve_inputs(workflow_inputs)
        print(f'self.params: {self.params}')
        print(f'workflow_inputs: {workflow_inputs}')
        #print(f'resolved_inputs: {resolved_inputs}')
        #workflow_outputs = {(_shortname(output.outputSource, True), output.type)
        #                    for output in self.cwl.outputs}
        workflow_outputs = {_shortname(output.outputSource, True) for output in self.cwl.outputs}
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
        print(f'step name: {step_name}')
        step_inputs = {_shortname(input_.source) for input_ in step.in_}
        print(f'step inputs: {step_inputs}')
        step_outputs = {f"{step_name}/{_shortname(output.id)}" for output in step_cwl.outputs}
        print(f'step outputs: {step_outputs}')
        step_hints = self.parse_requirements(step.hints, as_hints=True).union(
            self.parse_requirements(step_cwl.hints, as_hints=True)
        )
        step_requirements = self.parse_requirements(step.requirements).union(
            self.parse_requirements(step_cwl.requirements)
        )

        return wfi.add_task(step_name, hints=step_hints, requirements=step_requirements,
                            inputs=step_inputs, outputs=step_outputs)

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
    def parse_requirements(requirements, as_hints=False):
        """Parse CWL hints/requirements.

        :param requirements: the CWL requirements dictionary
        :type requirements: list of ordereddict
        :param as_hints: parse as hints instead of requirements
        :type as_hints: bool
        :rtype: set of Hint or set of Requirement or None
        """
        reqs = set()
        if not requirements:
            return reqs
        if as_hints:
            for req in requirements:
                pairs = ((k, v) for k, v in req.items() if k != "class")
                for pair in pairs:
                    reqs.add(Hint(req["class"], pair[0], pair[1]))
        else:
            for req in requirements:
                pairs = ((k, v) for k, v in req.items() if k != "class")
                for pair in pairs:
                    reqs.add(Requirement(req["class"], pair[0], pair[1]))

        return reqs


def _shortname(uri, output_source=False):
    """Shorten a CWL object URI.

    e.g., file:///path/to/file#step/name -> step/name,
    or file:///path/to/file#output/output/source -> output/source
    if outputSource is True

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
