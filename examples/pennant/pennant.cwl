cwlVersion: v1.0
class: CommandLineTool

baseCommand: pennant

inputs:
  pnt:
    type: File
    inputBinding: {}
stdout: pennant.txt
outputs:
  output:
    type: stdout
