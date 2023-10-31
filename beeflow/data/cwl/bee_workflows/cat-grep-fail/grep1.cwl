#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: grep
stdout: occur1.txt
inputs:
  word:
    type: string
    inputBinding:
      position: 1
  text_file:
    type: File
    inputBinding:
      position: 2
outputs:
  occur:
    type: stdout
