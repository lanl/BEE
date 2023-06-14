cwlVersion: v1.0
class: CommandLineTool

baseCommand: /PENNANT/build/pennant

inputs:
  pnt:
    type: File
    inputBinding: {}
stdout: pennant_2_node.out
outputs:
  output:
    type: stdout
