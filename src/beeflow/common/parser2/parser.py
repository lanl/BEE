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
import re
import yaml
import cwl_utils.parser_v1_2 as cwl_parser
import beeflow.common.wf_interface as wfi
from beeflow.common.wf_data import Hint, Requirement

type_table = {
    'string': str,
    'int': int,
    'long': int,
    'float': float,
    'double': float,
    'array': list,
    'record': dict,
    'File': str,
    'Directory': str,
    'Any': None
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
        """
        self.cwl = cwl_parser.load_document(cwl)
        if job:
            # Parse input job params into self.params
            self.parse_job(job)

        if self.cwl.class_ != "Workflow":
            raise ValueError("CWL class must be Workflow")

        def shortname(uri, output_source=False):
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
            else:
                return uri.split("#")[-1]

        workflow_name = os.path.basename(cwl).split(".")[0]
        # Steven had tuples, I changed to dict to mirror output of parse_job
        workflow_inputs = {shortname(input_.id): input_.type for input_ in self.cwl.inputs}
        resolved_inputs = self.resolve_inputs(workflow_inputs)
        print(f'self.params: {self.params}')
        print(f'workflow_inputs: {workflow_inputs}')
        print(f'resolved_inputs: {resolved_inputs}')
        workflow_outputs = {(shortname(output.outputSource, True), output.type)
                            for output in self.cwl.outputs}

        workflow_steps = [self.parse_step(step) for step in self.cwl.steps]


    def resolve_inputs(self, wf_inputs):
        rv = {}
        for k, v in wf_inputs.items():
            types = {'int': int, 'float': float, 'string': str}
            print(f'inputs k: {k}   v: {v}')
            print(f'type(v):   {types[v]}')
            print(f'params[{k}]: {self.params[k]}')
            print(f'type(params[{k}]): {type(self.params[k])}')
            if not isinstance(self.params[k], types[v]):
                raise ValueError(f'Types of input/param do not match: {v}/{self.params[k]}')
            rv[k] = self.params[k]
        return rv


    def parse_step(self, step):
        """Parse a CWL step object.

        :param step: the CWL step object
        :type step: WorkflowStep
        """
        step_cwl = cwl_parser.load_document(step.run)

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
            if not (isinstance(v, str) or isinstance(v, int) or isinstance(v, float)):
                raise ValueError(f'Invalid input job parameter type: {type(v)}')


def parse_args(args=sys.argv[1:]):
    """Parse arguments."""
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__)

    parser.add_argument("wf_file", type=str, help="CWL workflow file")
    parser.add_argument("wf_inputs", type=str, help="Workflow job file")

    return parser.parse_args(args)


def main():
    wf = CwlParser()
    args = parse_args()
    wf.parse_workflow(args.wf_file, args.wf_inputs)


if __name__ == "__main__":
    sys.exit(main())
