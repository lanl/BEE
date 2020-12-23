# -*- mode: YAML; -*-
#/clamr/CLAMR-master/clamr_cpuonly -n 32 -l 3 -t 5000 -i 10 -g 25 -G png

class: CommandLineTool
cwlVersion: v1.0

baseCommand: /users/trandles/CLAMR/clamr_cpuonly
stdout: clamr-stdout.txt
inputs:
  amr-type:
    type: string?
    inputBinding:
      prefix: -A
  grid-res:
    type: int?
    inputBinding:
      prefix: -n
  max-levels:
    type: int?
    inputBinding:
      prefix: -l
  time-steps:
    type: int?
    inputBinding:
      prefix: -t
  steps-between-output:
    type: int?
    inputBinding:
      prefix: -i
  steps-between-graphics:
    type: int?
    inputBinding:
      prefix: -g
  graphics-type:
    type: string?
    inputBinding:
      prefix: -G
  rollback-images:
    type: int?
    inputBinding:
      prefix: -b
  checkpoint-disk-interval:
    type: int?
    inputBinding:
      prefix: -c
  checkpoint-mem-interval:
    type: int?
    inputBinding:
      prefix: -C
  hash-method:
    type: string?
    inputBinding:
      prefix: -e
  
outputs:
  clamr-output:
    type: Directory
    outputBinding:
      glob: "graphics_output"
  clamr-stdout:
    type: stdout
  clamr-time-log:
    type: File
    outputBinding:
      glob: total_execution_time.log
