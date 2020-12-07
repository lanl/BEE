# -*- mode: yaml; -*-

# cwltool scatter-strings.cwl scatter-strings-job.yml

class: Workflow
cwlVersion: v1.0

requirements:
  ScatterFeatureRequirement: {}

inputs:
  deck_array: string[]

outputs: []

steps:
  crank:
    run:
      class: CommandLineTool
      inputs:
        deck:
          type: string
          inputBinding:
            position: 1
      outputs: []
      baseCommand: echo
    scatter: deck
    in:
      deck: deck_array
    out: []
