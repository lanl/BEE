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
            {"prefix": "-f", "position": 1},
            "inputBinding:\n  position: 1\n  prefix: -f\n",
            {"inputBinding": {"position": 1, "prefix": "-f"}},
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
