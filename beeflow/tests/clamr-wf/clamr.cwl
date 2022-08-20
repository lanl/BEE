# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

baseCommand: /clamr/CLAMR-master/clamr_cpuonly
stdout: clamr_stdout.txt
inputs:
  amr_type:
    type: string?
    inputBinding:
      prefix: -A
  grid_res:
    type: int?
    inputBinding:
      prefix: -n
  max_levels:
    type: int?
    inputBinding:
      prefix: -l
  time_steps:
    type: int?
    inputBinding:
      prefix: -t
  output_steps:
    type: int?
    inputBinding:
      prefix: -i
  graphic_steps:
    type: int?
    inputBinding:
      prefix: -g
  graphics_type:
    type: string?
    inputBinding:
      prefix: -G
  rollback_images:
    type: int?
    inputBinding:
      prefix: -b
  checkpoint_disk_interval:
    type: int?
    inputBinding:
      prefix: -c
  checkpoint_mem_interval:
    type: int?
    inputBinding:
      prefix: -C
  hash_method:
    type: string?
    inputBinding:
      prefix: -e
  
outputs:
  stdout:
    type: stdout
  outdir:
    type: Directory
    outputBinding:
      glob: graphics_output
  time_log:
    type: File
    outputBinding:
      glob: total_execution_time.log
