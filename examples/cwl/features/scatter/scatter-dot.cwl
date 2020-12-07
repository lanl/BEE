# -*- mode: yaml; -*-

class: Workflow
cwlVersion: v1.0

requirements:
  ScatterFeatureRequirement: {}

inputs:
  deck_array: string[]
  dir_array: string[]

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
        dir:
          type: string
          inputBinding:
            position: 2
      outputs: []
      baseCommand: echo
    scatter: [deck, dir]
    scatterMethod: dotproduct
    # also try nested_crossproduct and flat_crossproduct
    in:
      deck: deck_array
      dir: dir_array
    out: []
