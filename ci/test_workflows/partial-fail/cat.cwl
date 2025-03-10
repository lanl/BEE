#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: cat 
stdout: cat.txt
inputs:
  text_file:
    type: File
    inputBinding:
      position: 1
outputs:
  cat_out:
    type: stdout
