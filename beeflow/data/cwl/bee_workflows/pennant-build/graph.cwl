cwlVersion: v1.0
class: CommandLineTool

baseCommand: /graph_pennant.sh

inputs:
  out1node:
    type: File
    inputBinding:
      position: 1
  out2node:
    type: File
    inputBinding:
      position: 2
  out4node:
    type: File
    inputBinding:
      position: 3
  out8node:
    type: File
    inputBinding:
      position: 4
outputs:
  image:
    type: File
    outputBinding:
      glob: graph.png
