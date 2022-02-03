# This workflow has a fixed number of tasks and a fixed container type
class: Workflow
cwlVersion: v1.0

inputs:
  nw_file: string

outputs:
  nw_stdout:
    type: File
    outputSource: nwchem/nw_stdout

steps:
  nwchem:
    run: nwchem_bin.cwl
    in:
      nw_file: nw_file
    out: [nw_stdout]
    hints:
      DockerRequirement:
        # This is an x86 container (it's about ~1200MB so it will take a while to pull)
        dockerPull: "jtronge/nwchem:05aafc87223af82f58865d8b0f924dabd1adacbc"
      beeflow:MPIRequirement:
        nodes: 1
        ntasks: 2
        version: pmix_v3
