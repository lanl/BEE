cwlVersion: v1.0
class: CommandLineTool

baseCommand: pennant

inputs:
  pnt:
    type: File
    inputBinding: {}
stdout: pennant_4_node.out
outputs:
  output:
    type: stdout
