cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python", "-m", "add"]

inputs:
  x:
    type: int
    inputBinding:
      position: 1
  y:
    type: int
    inputBinding:
      position: 2

stdout: cwl.output.json

outputs:
  answer:
    type: int