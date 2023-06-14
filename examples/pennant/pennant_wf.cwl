cwlVersion: v1.0
class: Workflow

inputs:
  pnt: File

outputs:
  output_1_node:
    type: File
    outputSource: pennant_1_node/output
  output_2_node:
    type: File
    outputSource: pennant_2_node/output
  output_4_node:
    type: File
    outputSource: pennant_4_node/output
  output_8_node:
    type: File
    outputSource: pennant_8_node/output

steps:
  pennant_1_node:
    run: pennant_1_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 1
      DockerRequirement:
        beeflow:useContainer: "..."
  pennant_2_node:
    run: pennant_2_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 2
      DockerRequirement:
        beeflow:useContainer: "..."
  pennant_4_node:
    run: pennant_4_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 4
      DockerRequirement:
        beeflow:useContainer: "..."
  pennant_8_node:
    run: pennant_8_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 8
      DockerRequirement:
        beeflow:useContainer: "..."
