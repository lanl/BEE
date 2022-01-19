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
        # This is an x86 container
        dockerPull: "jtronge/nwchem:test-tce-ccsd"
      beeflow:MPIRequirement:
        ntasks: 2
