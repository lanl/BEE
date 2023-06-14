cwlVersion: v1.0
class: CommandLineTool

baseCommand: pennant

inputs:
  pnt:
    type: File
    inputBinding: {}
stdout: pennant_2_node.out
outputs:
  output:
    type: stdout
