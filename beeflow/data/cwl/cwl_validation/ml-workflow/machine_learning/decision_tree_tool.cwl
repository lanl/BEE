cwlVersion: v1.0
class: CommandLineTool
baseCommand: ["python", "/home/bee/cwl2/decision_tree.py"]

inputs:
  x:
    type: int
    inputBinding:
      position: 1

stdout: decision_tree_output.txt

outputs:
  answer:
    type: stdout
