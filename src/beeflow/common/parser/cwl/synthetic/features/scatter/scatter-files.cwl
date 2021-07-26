# -*- mode: yaml; -*-

# cwltool scatter-files.cwl scatter-files-job.ym

class: Workflow
cwlVersion: v1.0

requirements:
  ScatterFeatureRequirement: {}

inputs:
  file_array: File[]

outputs: []

steps:
  crank:
    run:
      class: CommandLineTool
      inputs:
        file:
          type: File
          inputBinding:
            position: 1
      outputs: []
      baseCommand: cat
    scatter: file
    in:
      file: file_array
    out: []
