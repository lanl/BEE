#!/usr/bin/env cwl-runner 
cwlVersion: v1.1.0-dev1
class: CommandLineTool
baseCommand: echo
input:
  message:
    type: string
    inputBinding:
      position: 1
outputs: []
