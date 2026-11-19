"""Workflow description parsers.

Contains two parsers:

* CwlParser: parses the contents of a CWL file and generates the graph
  representation of parsed workflows and tools in the graph database. This
  parser supports a subset of the CWL v1.0 standard. It is inspired by the
  CWL parser written by the SABER team at John Hopkins University (see SABER
  project at https://github.com/aplbrain/saber).

* BeeParser: converts a BEE python workflow specification (built with the
  python workflow description API in beeflow.common.cwl.workflow or the new
  beeflow.common.workflow_api) directly into the Workflow and Task objects
  consumed by the WorkflowInterface, without generating or parsing any CWL.
"""

# This module holds both the CWL parser and the python API parser
# pylint: disable=too-many-lines

import sys
import argparse
import importlib.util
import json
import os
import traceback
from pathlib import Path
import yaml
import cwl_utils.parser.cwl_v1_2 as cwl_parser
from schema_salad.exceptions import ValidationException

from beeflow.common import workflow_api
from beeflow.common.cwl.workflow import Workflow as WorkflowSpec
from beeflow.common.object_models import (
        Workflow,
        Task,
        InputParameter,
        OutputParameter,
        StepInput,
        StepOutput,
        Hint,
        Requirement,
        generate_workflow_id,
        get_requirement,
        )

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

    def parse_workflow(self, workflow_id, workflow_name, cwl_path,
                       job=None, workdir=".", wf_path="."):
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
                raise CwlParseError(
                        f"input {input_id} is missing from workflow job file"
                        )
            if not isinstance(value, type_map[type_]):
                raise CwlParseError(
                        "Input/param types do not match: " f"{input_id}/{value}"
                        )
            return value

        workflow_inputs = [
                InputParameter(
                    id=_shortname(input_.id),
                    type=input_.type,
                    value=resolve_input(input_, input_.type),
                    )
                for input_ in self.cwl.inputs
                ]
        workflow_outputs = [
                OutputParameter(
                    id=_shortname(output.id),
                    type=output.type,
                    value=None,
                    source=_shortname(output.outputSource, True),
                    )
                for output in self.cwl.outputs
                ]
        workflow_hints = self.parse_requirements(self.cwl.hints, as_hints=True)
        workflow_requirements = self.parse_requirements(self.cwl.requirements)

        workflow = Workflow(
                name=workflow_name,
                hints=workflow_hints,
                requirements=workflow_requirements,
                inputs=workflow_inputs,
                outputs=workflow_outputs,
                id=workflow_id,
                workdir=workdir,
                main_cwl=str(cwl_path),
                wf_path=str(wf_path),
                yaml=job,
                )
        tasks = [self.parse_step(step, workflow_id, workdir) for step in self.cwl.steps]

        return workflow, tasks

    def parse_step(self, step, workflow_id, workdir):
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
                step_input.id = step_input.id.replace(
                        step_shortname, step_shortname.split("/")[-1]
                        )

        if step_cwl.class_ != "CommandLineTool":
            raise CwlParseError(f"Step {step.id} class must be CommandLineTool")

        step_name = os.path.basename(step_id).split(".")[0]
        step_command = step_cwl.baseCommand
        step_inputs = self.parse_step_inputs(step.in_, step_cwl.inputs)
        step_requirements = self.parse_requirements(step.requirements)
        step_requirements.extend(self.parse_requirements(step_cwl.requirements))
        step_hints = self.parse_requirements(step.hints, as_hints=True)
        step_hints.extend(self.parse_requirements(step_cwl.hints, as_hints=True))
        step_workdir = resolve_step_workdir(
                get_requirement(
                    step_requirements,
                    step_hints,
                    "beeflow:TaskRequirement",
                    "workdir",
                    default="",
                    ),
                workdir,
                )

        # When using container do not add the path to the output
        # This can be changed when we fix binding for containers
        if any(hint.class_ == "DockerRequirement" for hint in step_hints):
            step_outputs = self.parse_step_outputs(
                    step.out, step_cwl.outputs, step_cwl.stdout, step_cwl.stderr
                    )
        else:
            step_outputs = self.parse_step_outputs(
                    step.out,
                    step_cwl.outputs,
                    step_cwl.stdout,
                    step_cwl.stderr,
                    workdir=step_workdir,
                    )
        step_stdout = step_cwl.stdout
        step_stderr = step_cwl.stderr

        return Task(
                name=step_name,
                base_command=step_command,
                hints=step_hints,
                requirements=step_requirements,
                inputs=step_inputs,
                outputs=step_outputs,
                stdout=step_stdout,
                stderr=step_stderr,
                workflow_id=workflow_id,
                workdir=step_workdir,
                )

    def parse_job(self, job):
        """Parse a CWL input job file.

        Input parameters are stored in the params attribute.

        :param job: the path of the input job file (YAML or JSON)
        :type job: str
        """
        self.params = load_job_inputs(job)

    @staticmethod
    def parse_step_inputs(cwl_in, step_inputs):
        """Parse step inputs from CWL step input objects.

        :param cwl_in: the step inputs from the Workflow file
        :type cwl_in: list of WorkflowStepInput
        :param step_inputs: the step inputs from the CommandLineTool file
        :type step_inputs: list of CommandInputParameter
        :rtype: list of StepInput
        """
        source_map = {
                _shortname(input_.id).split("/")[-1]: _shortname(input_.source)
                for input_ in cwl_in
                }

        inputs = []
        for step_input in step_inputs:
            # If the input type is str, then the input is required
            # If it is a list containing 'null' and another type(s) then it is optional
            # If the input is not in the source_map but has a default value then it will
            # be set by the GDB later
            if _shortname(step_input.id) not in source_map.keys():
                if isinstance(step_input.type, str) and step_input.default is None:
                    raise CwlParseError(
                            f"required input {_shortname(step_input.id)} " "not satisfied"
                            )
                continue

            if isinstance(step_input.type, str):
                input_type = step_input.type
            else:
                input_type = step_input.type[1]

            if step_input.inputBinding:
                inputs.append(
                        StepInput(
                            id=_shortname(step_input.id),
                            type=input_type,
                            value=None,
                            default=step_input.default,
                            source=source_map[_shortname(step_input.id)],
                            prefix=step_input.inputBinding.prefix,
                            position=step_input.inputBinding.position,
                            value_from=step_input.inputBinding.valueFrom,
                            )
                        )
            else:
                inputs.append(
                        StepInput(
                            id=_shortname(step_input.id),
                            type=input_type,
                            value=None,
                            default=step_input.default,
                            source=source_map[_shortname(step_input.id)],
                            prefix=None,
                            position=None,
                            value_from=None,
                            )
                        )
        return inputs

    @staticmethod
    def parse_step_outputs(cwl_out, step_outputs, stdout, stderr, workdir=None):
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
        out_map = {
                (
                    _shortname(step_output.id)
                    if _shortname(step_output.id).startswith(short_id + "/")
                    else short_id + "/" + _shortname(step_output.id)
                    ): step_output
                for step_output in step_outputs
                }

        outputs = []
        for out in out_short:
            if out not in out_map.keys():
                raise CwlParseError(
                        f"specified step output {out} not produced by CommandLineTool"
                        )

            output_type = out_map[out].type
            glob = ""
            if output_type == "stdout":
                if not stdout:
                    raise CwlParseError(
                            f"stdout capture required for step output {out} "
                            "but not specified by CommandLineTool"
                            )
                # Fill in glob with value of stdout
                glob = stdout
            elif output_type == "stderr":
                if not stderr:
                    raise ValueError(
                            (
                                f"stderr capture required for step output {out} "
                                "but not specified by CommandLineTool"
                                )
                            )
                # Fill in glob with value of stderr
                glob = stderr
            else:
                if out_map[out].outputBinding:
                    glob = out_map[out].outputBinding.glob

            if workdir is not None:
                glob = os.path.abspath(os.path.join(workdir, glob))

            outputs.append(StepOutput(id=out, type=output_type, value=None, glob=glob))
        return outputs

    def _read_requirement_file(self, key, items):
        """Read in a requirement file and replace it in the parsed items."""
        base_path = os.path.dirname(self.path)
        fname = items[key]
        path = os.path.join(base_path, fname)
        try:
            with open(path, encoding="utf-8") as fp:
                items[key] = fp.read()
        except FileNotFoundError:
            msg = f"Could not find a file for {key}: {fname}"
            raise CwlParseError(msg) from None
        if key in {"pre_script", "post_script"}:
            validate_prepost_shell_env(key, items, fname)

    def _resolve_requirement_file(self, key, items):
        """Resolve a requirement file path relative to the CWL file."""
        base_path = Path(self.path).parent
        path = Path(items[key]).expanduser()
        if not path.is_absolute():
            path = base_path / path
        path = path.resolve()
        items[key] = str(path)

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
                    if k != "class" and v is not None:
                        if isinstance(v, (int, float)):
                            items[k] = v
                        else:
                            items[k] = str(v)

                # Load in the dockerfile at parse time
                if "dockerFile" in items:
                    self._read_requirement_file("dockerFile", items)
                # Load the sbatch if added at parse time. This might not work well?
                if "sbatch" in items:
                    self._resolve_requirement_file("sbatch", items)
                # Load in pre/post scripts and make sure shell option is defined in cwl file
                if "pre_script" in items and items["enabled"]:
                    if "shell" in items:
                        self._read_requirement_file("pre_script", items)
                    else:
                        msg = (
                                "pre script enabled but shell option undefined in cwl file."
                                )
                        raise CwlParseError(msg) from None
                if "post_script" in items and items["enabled"]:
                    if "shell" in items:
                        self._read_requirement_file("post_script", items)
                    else:
                        msg = "post script enabled but shell option undefined in cwl file."
                        raise CwlParseError(msg) from None
                if "beeflow:bindMounts" in items:
                    self._read_requirement_file("beeflow:bindMounts", items)
                # Validate beeflow:WorkloadRequirement fields
                validate_workload_requirement(req["class"], items)
                reqs.append(Hint(class_=req["class"], params=items))
        else:
            for req in requirements:
                params = {
                    k: str(v)
                    for k, v in vars(req).items()
                    if k not in ("extension_fields", "loadingOptions", "class_")
                    and v is not None
                }
                # Validate beeflow:WorkloadRequirement fields
                validate_workload_requirement(req.class_, params)
                reqs.append(
                        Requirement(
                            class_=req.class_,
                            params=params,
                            )
                        )
        return reqs


def load_job_inputs(job, error_cls=CwlParseError):
    """Load input job parameters from a YAML or JSON file.

    :param job: the path of the input job file (YAML or JSON)
    :type job: str
    :param error_cls: the exception class used to report parse errors
    :type error_cls: Exception
    :rtype: dict
    """
    if job.endswith(".yml") or job.endswith(".yaml"):
        with open(job, encoding="utf-8") as fp:
            params = yaml.full_load(fp)
    elif job.endswith(".json"):
        with open(job, encoding="utf-8") as fp:
            params = json.load(fp)
    else:
        raise error_cls(
                "Unsupported input job file extension (only .yml "
                "and .json supported)"
                )

    for k, v in params.items():
        if not isinstance(k, str):
            raise error_cls(f"Invalid input job key: {str(k)}")
        if not isinstance(v, (str, int, float)):
            raise error_cls(f"Invalid input job parameter type: {type(v)}")
    return params


def validate_prepost_shell_env(key, items, fname, error_cls=CwlParseError):
    """Validate defined shell interpreters.

    :param key: the requirement parameter name (pre_script or post_script)
    :type key: str
    :param items: the requirement parameters
    :type items: dict
    :param fname: name of pre/post script file
    :type fname: str
    :param error_cls: the exception class used to report parse errors
    :type error_cls: Exception
    """
    env_decl = items[key].splitlines()
    # Need to remove whitespaces/newlines from list
    env_decl = [x for x in env_decl if x.strip()]
    # Check for shebang line in pre/post scripts
    if not env_decl[0].startswith("#!"):
        msg = f"No shebang line found in {fname}"
        raise error_cls(msg) from None
    # Now check for matching shell and shebang line values
    shell_val = "#!" + items["shell"]
    shebang_val = env_decl[0]
    if shell_val != shebang_val:
        msg = (
                f"CWL file shell {shell_val} does not match {fname} shell {shebang_val}"
                )
        raise error_cls(msg) from None
    # Remove shebang lines from scripts
    rm_line = env_decl[1:]
    # List to string format
    rm_line = "\n".join(rm_line)
    items.update({key: rm_line})


def validate_workload_requirement(req_class, items, error_cls=CwlParseError):
    """Validate beeflow:WorkloadRequirement fields.

    :param req_class: the requirement class name
    :type req_class: str
    :param items: the requirement parameters
    :type items: dict
    :param error_cls: the exception class used to report parse errors
    :type error_cls: Exception
    """
    if req_class != 'beeflow:WorkloadRequirement':
        return

    # Validate mode field if present
    if 'mode' in items:
        mode = items['mode']
        if not isinstance(mode, str):
            raise error_cls(
                'beeflow:WorkloadRequirement mode must be a string. '
                'Supported modes are "baremetal" and "scheduler".'
            )
        mode_lower = mode.lower()
        if mode_lower not in ('baremetal', 'scheduler'):
            raise error_cls(
                f'Unsupported beeflow:WorkloadRequirement mode {mode!r}. '
                'Supported modes are "baremetal" and "scheduler".'
            )

    # Validate scheduler field if present
    if 'scheduler' in items:
        scheduler = items['scheduler']
        if not isinstance(scheduler, str):
            raise error_cls(
                'beeflow:WorkloadRequirement scheduler must be a string.'
            )


def bee_value_type(value):
    """Return the BEE type name for a python API param/input value.

    :param value: a static value or an OutputRef
    :type value: str or int or float or workflow_api.OutputRef
    :rtype: str
    """
    if isinstance(value, workflow_api.OutputRef):
        return "File"
    return {str: "string", int: "int", float: "float"}.get(type(value), "string")


class BeeParseError(Exception):
    """Python workflow specification parser error class."""

    def __init__(self, *args):
        """Create a python specification parser error."""
        self.args = args


def _find_workflow_spec(module, path):
    """Find the Workflow object defined by a python workflow module.

    The module can either assign a Workflow object to a module-level
    'workflow' variable, return one from a main() or build() function, or
    define exactly one Workflow object.

    :param module: the loaded python workflow module
    :type module: module
    :param path: the path of the workflow specification file
    :type path: str
    :rtype: WorkflowSpec
    """
    workflow = getattr(module, "workflow", None)
    if isinstance(workflow, (WorkflowSpec, workflow_api.Workflow)):
        return workflow
    for func_name in ("build", "main"):
        func = getattr(module, func_name, None)
        if callable(func):
            result = func()
            if isinstance(result, (WorkflowSpec, workflow_api.Workflow)):
                return result
            workflow = getattr(module, "workflow", None)
            if isinstance(workflow, (WorkflowSpec, workflow_api.Workflow)):
                return workflow
    workflows = [
            obj for obj in vars(module).values()
            if isinstance(obj, (WorkflowSpec, workflow_api.Workflow))
            ]
    if len(workflows) == 1:
        return workflows[0]
    raise BeeParseError(
            f"{path} does not define a workflow: assign a Workflow object to a "
            "module-level 'workflow' variable or return one from main()"
            )


class BeeParser:
    """Class for parsing BEE python workflow specifications.

    Converts a Workflow object built with the python workflow description API
    (beeflow.common.cwl.workflow) directly into the Workflow and Task objects
    consumed by the WorkflowInterface. No CWL is generated or parsed.
    """

    def __init__(self):
        """Initialize the python workflow specification parser."""
        self.spec = None
        self.path = None
        self.params = {}

    def parse_workflow(self, workflow_id, workflow_name, spec, job=None,
                       workdir=".", wf_path="."):
        """Parse a python workflow specification into WF_Interface objects.

        Returns a tuple of the Workflow and the list of Task objects that can
        be loaded into the WorkflowInterface.

        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param workflow_name: the workflow name (defaults to the spec name)
        :type workflow_name: str
        :param spec: the Workflow object or path to a .py workflow specification
        :type spec: WorkflowSpec or str or pathlib.Path
        :param job: the input job file (YAML or JSON)
        :type job: str
        :param workdir: the workflow working directory
        :type workdir: str
        :param wf_path: the workflow directory or archive path
        :type wf_path: str
        :rtype: (Workflow, list of Task)
        """
        self.spec, self.path = self._load_spec(spec)
        self.params = load_job_inputs(job, BeeParseError) if job else {}

        if isinstance(self.spec, workflow_api.Workflow):
            return self._parse_bee_spec(workflow_id, workflow_name, job, workdir, wf_path)

        tasks = [self.parse_task(task, workflow_id, workdir) for task in self.spec.tasks]
        workflow = Workflow(
                name=workflow_name or self.spec.name,
                hints=[],
                requirements=[],
                inputs=self.workflow_inputs(self.spec.tasks),
                outputs=self.workflow_outputs(self.spec.tasks),
                id=workflow_id,
                workdir=workdir,
                main_cwl=self.path,
                wf_path=str(wf_path),
                yaml=job,
                )
        return workflow, tasks

    @staticmethod
    def _load_spec(spec):
        """Load the workflow specification from a Workflow object or .py file.

        :param spec: the Workflow object or path to a .py workflow specification
        :type spec: WorkflowSpec or workflow_api.Workflow or str or pathlib.Path
        :rtype: (Workflow, str or None)
        """
        if isinstance(spec, (WorkflowSpec, workflow_api.Workflow)):
            return spec, None
        path = Path(spec)
        if not path.is_file():
            raise BeeParseError(f"workflow specification {spec} not found")
        module_spec = importlib.util.spec_from_file_location(f"bee_{path.stem}", path)
        module = importlib.util.module_from_spec(module_spec)
        try:
            module_spec.loader.exec_module(module)
        except Exception as err:  # pylint: disable=W0718
            raise BeeParseError(
                    f"error executing workflow specification {path}: {err}"
                    ) from None
        return _find_workflow_spec(module, str(path)), str(path.resolve())

    def _parse_bee_spec(self, workflow_id, workflow_name, job, workdir, wf_path):
        """Convert a workflow_api.Workflow into WF_Interface objects.

        :rtype: (Workflow, list of Task)
        """
        self._validate_bee_spec(self.spec)
        tasks = [
                self._parse_bee_task(task, workflow_id, workdir)
                for task in self.spec.tasks
                ]
        workflow = Workflow(
                name=workflow_name or self.spec.name,
                hints=[],
                requirements=[],
                inputs=self._bee_workflow_inputs(self.spec.tasks),
                outputs=self._bee_workflow_outputs(self.spec.tasks),
                id=workflow_id,
                workdir=workdir,
                main_cwl=self.path,
                wf_path=str(wf_path),
                yaml=job,
                )
        return workflow, tasks

    def _validate_bee_spec(self, spec):
        """Validate a workflow_api.Workflow specification.

        :param spec: the python API workflow specification
        :type spec: workflow_api.Workflow
        """
        if not spec.tasks:
            raise BeeParseError(f"workflow {spec.name} does not define any tasks")
        by_name = {task.name: task for task in spec.tasks}
        if len(by_name) != len(spec.tasks):
            raise BeeParseError("workflow task names must be unique")

        for task in spec.tasks:
            commands = task.command_list()
            if not commands or any(
                    not isinstance(command, str) or not command.strip()
                    for command in commands
                    ):
                raise BeeParseError(
                        f"task {task.name} must define a non-empty command string"
                        )
            if len(commands) > 1:
                raise BeeParseError(
                        f"task {task.name}: multiple commands are not yet "
                        "supported by the python workflow API"
                        )

            declared = task.declared_values()
            for name, value in declared.items():
                if isinstance(value, workflow_api.OutputRef):
                    producer = by_name.get(value.task_name)
                    if producer is None:
                        raise BeeParseError(
                                f"task {task.name} input {name!r} references "
                                f"unknown task {value.task_name!r}"
                                )
                    if value.output_name not in producer.outputs:
                        raise BeeParseError(
                                f"task {task.name} input {name!r} references "
                                f"missing output {value.id!r}"
                                )
                elif not isinstance(value, (str, int, float)):
                    raise BeeParseError(
                            f"task {task.name} input {name!r} has unsupported "
                            f"type {type(value)}"
                            )

            for placeholder in task.placeholders():
                if placeholder not in declared:
                    raise BeeParseError(
                            f"task {task.name} command references "
                            f"{{{placeholder}}} but no matching param or input "
                            "is declared"
                            )

            for dep in task.depends_on or []:
                if dep is not by_name.get(dep.name):
                    raise BeeParseError(
                            f"task {task.name} depends on a task "
                            f"{dep.name!r} that is not part of the workflow"
                            )
                # Phase 1: dependencies must be implied by data flow, since
                # the graph database infers edges from output references
                if not any(
                        isinstance(value, workflow_api.OutputRef)
                        and value.task_name == dep.name
                        for value in declared.values()
                        ):
                    raise BeeParseError(
                            f"task {task.name} depends on {dep.name!r} without "
                            "sharing any data; explicit non-data dependencies "
                            "are not yet supported"
                            )

    def _parse_bee_task(self, task, workflow_id, workdir):
        """Convert a workflow_api.Task into a Task object for the WF_Interface.

        :rtype: Task
        """
        command, step_inputs = self._bee_command_and_inputs(task)
        step_outputs = [
                StepOutput(
                    id=f"{task.name}/{name}",
                    type="File",
                    value=None,
                    glob=os.path.abspath(os.path.join(workdir, glob)) if glob else glob,
                    )
                for name, glob in task.outputs.items()
                ]
        return Task(
                name=task.name,
                base_command=command,
                hints=self._bee_task_hints(task),
                requirements=[],
                inputs=step_inputs,
                outputs=step_outputs,
                stdout=task.stdout,
                stderr=task.stderr,
                workflow_id=workflow_id,
                workdir=workdir,
                )

    @staticmethod
    def _bee_command_and_inputs(task):
        """Expand a python API task into a command and its StepInputs.

        The {name} placeholders are left in the command tokens; the Task
        command property fills them in from the input values at execution
        time (object_models.Task.command).

        :rtype: (list of str, list of StepInput)
        """
        command = task.command_list()[0].split()
        inputs = []
        for name, value in task.declared_values().items():
            if isinstance(value, workflow_api.OutputRef):
                source = value.id
                default = None
            else:
                source = name
                default = value
            inputs.append(
                    StepInput(
                        id=name,
                        type=bee_value_type(value),
                        value=None,
                        default=default,
                        source=source,
                        prefix=None,
                        position=None,
                        value_from=None,
                        )
                    )
        return command, inputs

    def _bee_task_hints(self, task):
        """Convert python API resources and scripts into Hint objects.

        :rtype: list of Hint
        """
        hints = []
        mpi_params = {}
        slurm_params = {}
        resources = task.resources
        if resources is not None:
            mpi_params = {
                    key: value
                    for key, value in (
                        ("nodes", resources.nodes),
                        ("ntasks", resources.ntasks),
                        ("tasks_per_node", resources.tasks_per_node),
                        )
                    if value is not None
                    }
            if resources.walltime is not None:
                slurm_params["timeLimit"] = resources.walltime
        for key, value in (task.scheduler_options or {}).items():
            if value is not None:
                slurm_params[key] = value
        if mpi_params:
            hints.append(Hint(class_="beeflow:MPIRequirement", params=mpi_params))
        if slurm_params:
            hints.append(Hint(class_="beeflow:SlurmRequirement", params=slurm_params))
        if task.pre_script is not None or task.post_script is not None:
            script_params = {"enabled": True, "shell": "/bin/bash"}
            if task.pre_script is not None:
                script_params["pre_script"] = task.pre_script
            if task.post_script is not None:
                script_params["post_script"] = task.post_script
            # Read the script files (relative to the spec) and validate the
            # shebang lines against the shell
            self._resolve_hint_files(script_params)
            hints.append(
                    Hint(class_="beeflow:ScriptRequirement", params=script_params)
                    )
        return hints

    def _bee_workflow_inputs(self, tasks):
        """Derive workflow inputs from the python API task params and inputs.

        A name becomes a workflow input when every task declaring it agrees
        on the value; names declared with conflicting values stay task-local.
        The job file, when given, overrides the workflow input value.

        :rtype: list of InputParameter
        """
        declared = {}
        for task in tasks:
            for name, value in task.declared_values().items():
                if isinstance(value, workflow_api.OutputRef):
                    continue
                entry = (bee_value_type(value), value)
                if declared.get(name, entry) != entry:
                    # Conflicting declarations: keep the value task-local
                    declared[name] = None
                    continue
                declared.setdefault(name, entry)
        inputs = []
        for name, entry in declared.items():
            if entry is None:
                continue
            type_, value = entry
            value = self.params.get(name, value)
            expected_type = type_map.get(type_)
            if expected_type is not None and not isinstance(value, expected_type):
                raise BeeParseError(
                        "Input/param types do not match: " f"{name}/{value}"
                        )
            inputs.append(InputParameter(id=name, type=type_, value=value))
        return inputs

    @staticmethod
    def _bee_workflow_outputs(tasks):
        """Derive workflow outputs from the python API task outputs.

        :rtype: list of OutputParameter
        """
        outputs = []
        for task in tasks:
            for name in task.outputs:
                output_id = f"{task.name}/{name}"
                outputs.append(
                        OutputParameter(
                            id=output_id,
                            type="File",
                            value=None,
                            source=output_id,
                            )
                        )
        return outputs

    def parse_task(self, task, workflow_id, workdir):
        """Convert a python API Task into a Task object for the WF_Interface.

        :param task: the python API task
        :type task: Task
        :param workflow_id: the workflow ID
        :type workflow_id: str
        :param workdir: the workflow working directory
        :type workdir: str
        :rtype: Task
        """
        hints, task_workdir = self.parse_task_hints(task.hints)
        step_workdir = resolve_step_workdir(task_workdir, workdir)
        # When using a container do not add the path to the output
        # This can be changed when we fix binding for containers
        use_container = any(hint.class_ == "DockerRequirement" for hint in hints)
        return Task(
                name=task.name,
                base_command=task.base_command,
                hints=hints,
                requirements=[],
                inputs=self.parse_task_inputs(task),
                outputs=self.parse_task_outputs(
                    task, workdir=None if use_container else step_workdir
                    ),
                stdout=task.stdout,
                stderr=task.stderr,
                workflow_id=workflow_id,
                workdir=step_workdir,
                )

    @staticmethod
    def parse_task_inputs(task):
        """Convert python API task inputs into StepInput objects.

        Inputs with a literal value reference a workflow input of the same
        name; the graph database fills in the value at execution time. Inputs
        with a source value (task/output) depend on another task's output.

        :param task: the python API task
        :type task: Task
        :rtype: list of StepInput
        """
        inputs = []
        for input_ in task.inputs:
            if input_.has_source():
                source = input_.value
                default = None
            else:
                source = input_.name
                default = input_.value
            inputs.append(
                    StepInput(
                        id=input_.name,
                        type=input_.type_,
                        value=None,
                        default=default,
                        source=source,
                        prefix=input_.prefix,
                        position=input_.position,
                        value_from=input_.value_from,
                        )
                    )
        return inputs

    @staticmethod
    def parse_task_outputs(task, workdir=None):
        """Convert python API task outputs into StepOutput objects.

        :param task: the python API task
        :type task: Task
        :param workdir: resolve relative globs against this workdir (None to skip)
        :type workdir: str
        :rtype: list of StepOutput
        """
        outputs = []
        for output in task.outputs:
            glob = output.glob
            if output.run_type == "stdout":
                glob = task.stdout
            elif output.run_type == "stderr":
                glob = task.stderr
            if workdir is not None and glob:
                glob = os.path.abspath(os.path.join(workdir, glob))
            outputs.append(
                    StepOutput(
                        id=f"{task.name}/{output.name}",
                        type=output.run_type,
                        value=None,
                        glob=glob,
                        )
                    )
        return outputs

    def parse_task_hints(self, hints):
        """Convert python API hints into Hint objects.

        Each python API hint provides a requirement() method that returns a
        requirement object whose dump() method returns the requirement class
        name and parameters used by the rest of BEE.

        :param hints: the python API hints
        :type hints: list
        :rtype: (list of Hint, str)
        """
        parsed = []
        task_workdir = ""
        for hint in hints or []:
            (class_, params), = hint.requirement().dump().items()
            params = {
                    key: value if isinstance(value, (int, float)) else str(value)
                    for key, value in params.items()
                    if value is not None
                    }
            self._resolve_hint_files(params)
            validate_workload_requirement(class_, params, BeeParseError)
            parsed.append(Hint(class_=class_, params=params))
            if class_ == "beeflow:TaskRequirement":
                task_workdir = params.get("workdir", "")
        return parsed, task_workdir

    def _hint_base_path(self):
        """Return the base path used to resolve hint file parameters."""
        return Path(self.path).parent if self.path else Path.cwd()

    def _read_hint_file(self, key, params):
        """Read in a hint file (relative to the spec) and store its contents."""
        fname = params[key]
        path = self._hint_base_path() / fname
        try:
            params[key] = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise BeeParseError(
                    f"Could not find a file for {key}: {fname}"
                    ) from None
        if key in {"pre_script", "post_script"}:
            validate_prepost_shell_env(key, params, fname, BeeParseError)

    def _resolve_hint_files(self, params):
        """Read or resolve file-based hint parameters.

        :param params: the requirement parameters
        :type params: dict
        """
        # Load the Dockerfile at parse time
        if "dockerFile" in params:
            self._read_hint_file("dockerFile", params)
        # Load the sbatch file at parse time
        if "sbatch" in params:
            params["sbatch"] = str(
                    (self._hint_base_path() / params["sbatch"]).resolve()
                    )
        # Load pre/post scripts and make sure the shell option is defined
        if "pre_script" in params and params["enabled"]:
            if "shell" not in params:
                raise BeeParseError(
                        "pre script enabled but shell option undefined in workflow spec."
                        )
            self._read_hint_file("pre_script", params)
        if "post_script" in params and params["enabled"]:
            if "shell" not in params:
                raise BeeParseError(
                        "post script enabled but shell option undefined in workflow spec."
                        )
            self._read_hint_file("post_script", params)
        if "beeflow:bindMounts" in params:
            self._read_hint_file("beeflow:bindMounts", params)

    def workflow_inputs(self, tasks):
        """Derive workflow inputs from the literal-valued task inputs.

        The job file, when given, overrides the literal value specified in the
        workflow specification.

        :param tasks: the python API tasks
        :type tasks: list of Task
        :rtype: list of InputParameter
        """
        inputs = []
        seen = {}
        for task in tasks:
            for input_ in task.inputs:
                if input_.has_source():
                    continue
                if input_.name in seen:
                    if seen[input_.name] != input_.type_:
                        raise BeeParseError(
                                f"conflicting types for workflow input "
                                f"{input_.name}: {seen[input_.name]} and {input_.type_}"
                                )
                    continue
                value = self.params.get(input_.name, input_.value)
                if value is None:
                    raise BeeParseError(
                            f"input {input_.name} is missing from the workflow spec "
                            "and job file"
                            )
                expected_type = type_map.get(input_.type_)
                if expected_type is not None and not isinstance(value, expected_type):
                    raise BeeParseError(
                            "Input/param types do not match: " f"{input_.name}/{value}"
                            )
                seen[input_.name] = input_.type_
                inputs.append(
                        InputParameter(id=input_.name, type=input_.type_, value=value)
                        )
        return inputs

    @staticmethod
    def workflow_outputs(tasks):
        """Derive workflow outputs from the sourced task outputs.

        Task outputs with a source (task/output) are exposed as workflow
        outputs, mirroring the source field of the python API Output class.

        :param tasks: the python API tasks
        :type tasks: list of Task
        :rtype: list of OutputParameter
        """
        outputs = []
        for task in tasks:
            for output in task.outputs:
                if not output.source:
                    continue
                # stdout/stderr outputs are exposed as files
                output_type = (
                        "File" if output.run_type in ("stdout", "stderr")
                        else output.run_type
                        )
                outputs.append(
                        OutputParameter(
                            id=output.name,
                            type=output_type,
                            value=None,
                            source=output.source,
                            )
                        )
        return outputs


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

    parser.add_argument(
            "wf_file", type=str, help="CWL workflow file or BEE python workflow specification"
            )
    parser.add_argument(
            "-i", "--inputs", type=str, help="Workflow job inputs file", required=False
            )

    return parser.parse_args(args)


def resolve_step_workdir(step_workdir, workdir):
    """Resolve step workdir relative to workflow workdir."""
    if not step_workdir or step_workdir.strip() == "":
        return workdir
    # should be redundant
    workdir = Path(workdir).expanduser().resolve()
    desired = Path(step_workdir).expanduser()
    if desired.is_absolute():
        return str(desired.resolve())
    return str((workdir / desired).resolve())


def main():
    """Run the parser on a CWL or python Workflow and job file directly."""
    wf_id = generate_workflow_id()
    args = parse_args()
    if args.wf_file.endswith(".py"):
        parser = BeeParser()
        # None lets the parser fall back to the name from the specification
        workflow, tasks = parser.parse_workflow(
                wf_id, None, args.wf_file, job=args.inputs
                )
    else:
        parser = CwlParser()
        workflow, tasks = parser.parse_workflow(
            wf_id, Path(args.wf_file).stem, args.wf_file, job=args.inputs
        )
    print("Parsed workflow:")
    print(workflow)

    print("Parsed tasks:")
    print(tasks)


if __name__ == "__main__":
    sys.exit(main())
