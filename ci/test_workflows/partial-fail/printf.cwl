#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: printf 
stdout: printf.txt
inputs:
  source:
    type: string
    inputBinding:
      position: 1
outputs:
  contents:
    type: stdout
