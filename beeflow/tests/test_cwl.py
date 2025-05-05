from beeflow.common.cwl import cwl
import pytest


@pytest.mark.parametrize(
    "fn, inputs, expected_repr, expected_dump",
    [
        (
            cwl.Header,
            {"class_type": "CommandLineTool", "cwl_version": "v1.2"},
            "cwlVersion: v1.2\nclass: CommandLineTool\n",
            {"cwlVersion": "v1.2", "class": "CommandLineTool"},
        ),
        (
            cwl.Input,
            {"input_name": "fname", "input_type": "string"},
            "fname: string\n",
            {"fname": "string"},
        ),
        (
            cwl.InputBinding,
            {"prefix": "-f", "position": 1, "value_from": '$("/graph%05d.png")'},
            'inputBinding:\n  position: 1\n  prefix: -f\n  valueFrom: $("/graph%05d.png")\n',
            {
                "inputBinding": {
                    "position": 1,
                    "prefix": "-f",
                    "valueFrom": '$("/graph%05d.png")',
                }
            },
        ),
        (
            cwl.RunInput,
            {
                "input_name": "fname",
                "input_type": "string",
                "source": "step1",
                "input_binding": cwl.InputBinding(prefix="-j", position=1),
            },
            "fname:\n  type: string\n  inputBinding:\n    position: 1\n    prefix: -j\n",
            {
                "fname": {
                    "type": "string",
                    "inputBinding": {"position": 1, "prefix": "-j"},
                }
            },
        ),
        (
            cwl.Output,
            {"output_name": "out", "output_type": "stdout"},
            "out:\n  type: stdout\n",
            {"out": {"type": "stdout"}},
        ),
        (
            cwl.CWLOutput,
            {"output_name": "out", "output_type": "stdout"},
            "out:\n  type: stdout\n",
            {"out": {"type": "stdout"}},
        ),
        (
            cwl.OutputBinding,
            {"prefix": "-o", "position": 1},
            "outputBinding:\n  position: 1\n  prefix: -o\n",
            {"outputBinding": {"position": 1, "prefix": "-o"}},
        ),
        (
            cwl.RunOutput,
            {
                "output_name": "out",
                "output_type": "File",
                "output_binding": "filename.txt",
            },
            "out:\n  type: File\n  outputBinding:\n    glob: filename.txt\n",
            {
                "out": {
                    "type": "File",
                    "outputBinding": {"glob": "filename.txt"},
                }
            },
        ),
        (
            cwl.Inputs,
            {
                "inputs": [
                    cwl.Input("fname1", "string"),
                    cwl.Input("fname2", "string"),
                ],
            },
            "inputs:\n  fname1: string\n  fname2: string\n",
            {"inputs": {"fname1": "string", "fname2": "string"}},
        ),
        (
            cwl.Outputs,
            {
                "outputs": [
                    cwl.Output("fname1", "stdout"),
                    cwl.Output("fname2", "stdout"),
                ],
            },
            "outputs:\n  fname1:\n    type: stdout\n  fname2:\n    type: stdout\n",
            {"outputs": {"fname1": {"type": "stdout"}, "fname2": {"type": "stdout"}}},
        ),
        (
            cwl.DockerRequirement,
            {"docker_pull": "container-image"},
            "DockerRequirement:\n  dockerPull: container-image\n",
            {"DockerRequirement": {"dockerPull": "container-image"}},
        ),
        (
            cwl.DockerRequirement,
            {"copy_container": "path-to-container-image"},
            "DockerRequirement:\n  beeflow:copyContainer: path-to-container-image\n",
            {"DockerRequirement": {"beeflow:copyContainer": "path-to-container-image"}},
        ),
        (
            cwl.DockerRequirement,
            {"use_container": "path-to-container-image"},
            "DockerRequirement:\n  beeflow:useContainer: path-to-container-image\n",
            {"DockerRequirement": {"beeflow:useContainer": "path-to-container-image"}},
        ),
        (
            cwl.DockerRequirement,
            {
                "docker_file": "dockerfile-name",
                "container_name": "container-name",
                "force_type": "none",
            },
            "DockerRequirement:\n  dockerFile: dockerfile-name\n  beeflow:containerName: container-name\n  beeflow:forceType: none\n",
            {
                "DockerRequirement": {
                    "dockerFile": "dockerfile-name",
                    "beeflow:containerName": "container-name",
                    "beeflow:forceType": "none",
                }
            },
        ),
        (
            cwl.MPIRequirement,
            {"nodes": 1, "ntasks": 2},
            "beeflow:MPIRequirement:\n  nodes: 1\n  ntasks: 2\n",
            {"beeflow:MPIRequirement": {"nodes": 1, "ntasks": 2}},
        ),
        (
            cwl.SlurmRequirement,
            {
                "account": "my_account",
                "time_limit": 500,
                "partition": "gpu",
                "qos": "shared",
                "reservation": "my_reservation",
            },
            "beeflow:SlurmRequirement:\n  account: my_account\n  timeLimit: 500\n  partition: gpu\n  qos: shared\n  reservation: my_reservation\n",
            {
                "beeflow:SlurmRequirement": {
                    "account": "my_account",
                    "timeLimit": 500,
                    "partition": "gpu",
                    "qos": "shared",
                    "reservation": "my_reservation",
                }
            },
        ),
        (
            cwl.CheckpointRequirement,
            {
                "file_path": "checkpoint_output",
                "container_path": "checkpoint_output",
                "file_regex": "backup[0-9]*.crx",
                "restart_parameters": "-R",
                "num_tries": 2,
            },
            "beeflow:CheckpointRequirement:\n  enabled: true\n  file_path: checkpoint_output\n  container_path: checkpoint_output\n  file_regex: backup[0-9]*.crx\n  restart_parameters: -R\n  num_tries: 2\n",
            {
                "beeflow:CheckpointRequirement": {
                    "enabled": True,
                    "file_path": "checkpoint_output",
                    "container_path": "checkpoint_output",
                    "file_regex": "backup[0-9]*.crx",
                    "restart_parameters": "-R",
                    "num_tries": 2,
                }
            },
        ),
        (
            cwl.ScriptRequirement,
            {
                "pre_script": "pre.sh",
                "post_script": "post.sh",
                "enabled": True,
                "shell": "/bin/bash",
            },
            "beeflow:ScriptRequirement:\n  pre_script: pre.sh\n  post_script: post.sh\n  enabled: true\n  shell: /bin/bash\n",
            {
                "beeflow:ScriptRequirement": {
                    "pre_script": "pre.sh",
                    "post_script": "post.sh",
                    "enabled": True,
                    "shell": "/bin/bash",
                },
            },
        ),
        (
            cwl.Hints,
            {"hints": [cwl.MPIRequirement(1, 1)]},
            "hints:\n  beeflow:MPIRequirement:\n    nodes: 1\n    ntasks: 1\n",
            {"hints": {"beeflow:MPIRequirement": {"nodes": 1, "ntasks": 1}}},
        ),
        (
            cwl.Run,
            {
                "base_command": "cat",
                "inputs": cwl.Inputs(
                    [cwl.RunInput("input_file", "File", cwl.InputBinding())]
                ),
                "outputs": cwl.Outputs([cwl.RunOutput("contents", "stdout")]),
                "stdout": "cat.txt",
            },
            "run:\n  class: CommandLineTool\n  baseCommand: cat\n  stdout: cat.txt\n  inputs:\n    input_file:\n      type: File\n      inputBinding: {}\n  outputs:\n    contents:\n      type: stdout\n",
            {
                "run": {
                    "class": "CommandLineTool",
                    "baseCommand": "cat",
                    "stdout": "cat.txt",
                    "inputs": {"input_file": {"type": "File", "inputBinding": {}}},
                    "outputs": {"contents": {"type": "stdout"}},
                }
            },
        ),
        (
            cwl.Step,
            {
                "step_name": "step1",
                "run": cwl.Run(
                    "cat",
                    cwl.Inputs(
                        [cwl.RunInput("input_file", "File", cwl.InputBinding())]
                    ),
                    cwl.Outputs([cwl.RunOutput("contents", "stdout")]),
                    "cat.txt",
                ),
            },
            "step1:\n  run:\n    class: CommandLineTool\n    baseCommand: cat\n    stdout: cat.txt\n    inputs:\n      input_file:\n        type: File\n        inputBinding: {}\n    outputs:\n      contents:\n        type: stdout\n  in:\n    input_file: input_file\n  out: [contents]\n",
            {
                "step1": {
                    "run": {
                        "class": "CommandLineTool",
                        "baseCommand": "cat",
                        "stdout": "cat.txt",
                        "inputs": {"input_file": {"type": "File", "inputBinding": {}}},
                        "outputs": {"contents": {"type": "stdout"}},
                    },
                    "in": {"input_file": "input_file"},
                    "out": ["contents"],
                }
            },
        ),
        (
            cwl.Steps,
            {
                "steps": [
                    cwl.Step(
                        step_name="step1",
                        run=cwl.Run(
                            "cat",
                            cwl.Inputs(
                                [cwl.RunInput("input_file", "File", cwl.InputBinding())]
                            ),
                            cwl.Outputs([cwl.RunOutput("contents", "stdout")]),
                            "cat.txt",
                        ),
                    )
                ]
            },
            """steps:
  step1:
    run:
      class: CommandLineTool
      baseCommand: cat
      stdout: cat.txt
      inputs:
        input_file:
          type: File
          inputBinding: {}
      outputs:
        contents:
          type: stdout
    in:
      input_file: input_file
    out: [contents]
""",
            {
                "steps": {
                    "step1": {
                        "run": {
                            "class": "CommandLineTool",
                            "baseCommand": "cat",
                            "stdout": "cat.txt",
                            "inputs": {
                                "input_file": {"type": "File", "inputBinding": {}}
                            },
                            "outputs": {"contents": {"type": "stdout"}},
                        },
                        "in": {"input_file": "input_file"},
                        "out": ["contents"],
                    }
                }
            },
        ),
    ],
)
def test_repr_dump(fn, inputs, expected_repr, expected_dump):
    """Regression test CWL dataclasses for just repr, dump."""
    res = fn(**inputs)
    assert res.dump() == expected_dump
    assert repr(res) == expected_repr


def test_cwl_input():
    """Regression test CWLInput."""
    expected_repr = (
        "CWLInput(input_name='fname', input_type='string', value='my_file.txt')"
    )
    expected_dump = {"fname": "string"}
    expected_value = "my_file.txt"
    res = cwl.CWLInput(input_name="fname", input_type="string", value="my_file.txt")
    assert res.dump() == expected_dump
    assert repr(res) == expected_repr
    assert res.value == expected_value


def test_add_inputs():
    """Regression test Inputs __add__."""
    input1 = cwl.Input("fname1", "string")
    input2 = cwl.Input("fname2", "string")
    inputs1 = cwl.Inputs([input1])
    inputs2 = cwl.Inputs([input2])
    inputs_both = cwl.Inputs([input1, input2])
    assert inputs1 + inputs2 == inputs_both


def test_add_outputs():
    """Regression test Outputs __add__."""
    output1 = cwl.Output("fout1", "stdout")
    output2 = cwl.Output("fout1", "stdout")
    outputs1 = cwl.Outputs([output1])
    outputs2 = cwl.Outputs([output2])
    outputs_both = cwl.Outputs([output1, output2])
    assert outputs1 + outputs2 == outputs_both


def test_cwl_workflow():
    """Regression test CWL class dumps and repr."""
    expected_dump_wf = """cwlVersion: v1.0
class: Workflow

inputs:
  fname: string

outputs:
  out:
    type: stdout

steps:
  step1:
    run:
      class: CommandLineTool
      baseCommand: cat
      stdout: cat.txt
      inputs:
        input_file:
          type: File
          inputBinding: {}
      outputs:
        contents:
          type: stdout
    in:
      input_file: input_file
    out: [contents]
"""
    expected_dump_inputs = "fname: my_file.txt\n"
    cwl_input = cwl.CWLInput("fname", "string", "my_file.txt")
    cwl_output = cwl.CWLOutput("out", "stdout")
    run_input = cwl.RunInput("input_file", "File", cwl.InputBinding())
    run_output = cwl.RunOutput("contents", "stdout")
    steps = cwl.Steps(
        [
            cwl.Step(
                step_name="step1",
                run=cwl.Run(
                    "cat", cwl.Inputs([run_input]), cwl.Outputs([run_output]), "cat.txt"
                ),
            )
        ]
    )
    workflow = cwl.CWL(
        cwl_name="workflow",
        inputs=cwl.CWLInputs([cwl_input]),
        outputs=cwl.CWLOutputs([cwl_output]),
        steps=steps,
    )
    dump_wf = workflow.dump_wf()
    dump_inputs = workflow.dump_inputs()
    assert repr(workflow) == expected_dump_wf
    assert dump_wf == expected_dump_wf
    assert dump_inputs == expected_dump_inputs
