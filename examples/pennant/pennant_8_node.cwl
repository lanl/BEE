cwlVersion: v1.0
class: CommandLineTool

baseCommand: /PENNANT/build/pennant

inputs:
  pnt:
    type: File
    inputBinding: {}
stdout: pennant_8_node.out
outputs:
  output:
    type: stdout
