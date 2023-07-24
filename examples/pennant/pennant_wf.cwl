cwlVersion: v1.2
class: Workflow

inputs:
  pnt: File

outputs:
  output_1_node:
    type: File
    outputSource: 1_node/output
  output_2_node:
    type: File
    outputSource: 2_node/output
  output_4_node:
    type: File
    outputSource: 4_node/output
  image:
    type: File
    outputSource: graph/image

steps:
  1_node:
    run: pennant_1_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 1
      DockerRequirement:
        beeflow:useContainer: "$HOME/img/pennant.tar.gz"
  2_node:
    run: pennant_2_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 2
      DockerRequirement:
        beeflow:useContainer: "$HOME/img/pennant.tar.gz"
  4_node:
    run: pennant_4_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 4
      DockerRequirement:
        beeflow:useContainer: "$HOME/img/pennant.tar.gz"
  graph:
    run: graph.cwl
    in:
      out1node: 1_node/output
      out2node: 2_node/output
      out4node: 4_node/output
    out: [image]
    hints:
      DockerRequirement:
        beeflow:useContainer: "$HOME/img/pennant-graph.tar.gz"
