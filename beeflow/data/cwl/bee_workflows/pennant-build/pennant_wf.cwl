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
  output_8_node:
    type: File
    outputSource: 8_node/output
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
        dockerFile: "Dockerfile.pennant-flux-x86_64"
        beeflow:containerName: "pennant-flux"

  2_node:
    run: pennant_2_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 2
      DockerRequirement:
        dockerFile: "Dockerfile.pennant-flux-x86_64"
        beeflow:containerName: "pennant-flux"

  4_node:
    run: pennant_4_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 4
      DockerRequirement:
        dockerFile: "Dockerfile.pennant-flux-x86_64"
        beeflow:containerName: "pennant-flux"

  8_node:
    run: pennant_8_node.cwl
    in:
      pnt: pnt
    out: [output]
    hints:
      beeflow:MPIRequirement:
        nodes: 8
      DockerRequirement:
        dockerFile: "Dockerfile.pennant-flux-x86_64"
        beeflow:containerName: "pennant-flux"

  graph:
    run: graph.cwl
    in:
      out1node: 1_node/output
      out2node: 2_node/output
      out4node: 4_node/output
      out8node: 8_node/output
    out: [image]
    hints:
      DockerRequirement:
        dockerFile: "Dockerfile.pennant-graph-x86_64"
        beeflow:containerName: "pennant-graph"

