cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python", "/home/bee/cwl2/linear_regression.py"]

inputs:
  x:
    type: int
    inputBinding:
      position: 1

stdout: linear_regress_output.txt

outputs:
  answer:
    type: stdout
