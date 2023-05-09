#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: cat
stdout: cat.txt
stderr: cat.err
inputs:
  input_file:
    type: File
    inputBinding:
      position: 1
outputs:
  contents:
    type: stdout
  cat_stderr:
    type: stderr
