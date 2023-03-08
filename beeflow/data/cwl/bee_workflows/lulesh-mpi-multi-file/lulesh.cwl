class: CommandLineTool
cwlVersion: v1.0

baseCommand: [/lulesh2.0]
stdout: lulesh_stdout.txt
inputs:
  size:
    type: int
    inputBinding:
      prefix: -s
  iterations:
    type: int
    inputBinding:
      prefix: -i
outputs:
  lulesh_stdout:
    type: stdout
