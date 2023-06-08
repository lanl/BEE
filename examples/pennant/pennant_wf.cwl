cwlVersion: v1.0
class: Workflow

inputs:
  pnt: File

outputs:
  output-1-node:
    type: File
    outputSource: pennant-1-node/output
  output-2-node:
    type: File
    outputSource: pennant-2-node/output
  output-4-node:
    type: File
    outputSource: pennant-4-node/output
  output-8-node:
    type: File
    outputSource: pennant-8-node/output

steps:
  pennant-1-node:
    run: pennant.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 1
  pennant-2-node:
    run: pennant.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 2
  pennant-4-node:
    run: pennant.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 4
  pennant-8-node:
    run: pennant.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 8
