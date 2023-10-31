#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: tar-not-a-real-command-for-failure
inputs:
  tarball_fname: 
    type: string
    inputBinding:
      position: 1
      prefix: -cf
  file0:
    type: File
    inputBinding:
      position: 2
  file1:
    type: File
    inputBinding:
      position: 3
outputs:
  tarball:
    type: File
    outputBinding:
      glob: $(inputs.tarball_fname)
