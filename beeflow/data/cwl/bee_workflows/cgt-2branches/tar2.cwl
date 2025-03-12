#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: tar
inputs:
  tarball_fname2:
    type: string
    inputBinding:
      position: 1
      prefix: -cf
  file2:
    type: File
    inputBinding:
      position: 2
  file3:
    type: File
    inputBinding:
      position: 3
outputs:
  tarball2:
    type: File
    outputBinding:
      glob: $(inputs.tarball_fname2)
