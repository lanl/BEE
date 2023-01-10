#!/usr/bin/env cwl-runner

class: CommandLineTool
cwlVersion: v1.0

baseCommand: ['/bin/cat', '/etc/centos-release']
stdout: output.txt
inputs:
  get-release:
    type: boolean
    inputBinding:
      position: 1
outputs:
  release_output:
    type: stdout
requirements:
  DockerRequirement:
    dockerPull: centos:8
