#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: cat
stdout: cat2.txt
stderr: cat2.err
inputs:
  input_file2:
    type: File
    inputBinding:
      position: 1
outputs:
  contents:
    type: stdout
  cat_stderr2:
    type: stderr
