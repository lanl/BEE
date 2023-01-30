cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python", "/home/bee/cwl2/predict_code.py"]

inputs:
  x:
    type: int
    inputBinding:
      position: 1
  y:
    type: int
    inputBinding:
      position: 2
  z:
    type: int
    inputBinding:
      position: 3

stdout: expectedValue.txt

outputs:
  answer:
    type: stdout
