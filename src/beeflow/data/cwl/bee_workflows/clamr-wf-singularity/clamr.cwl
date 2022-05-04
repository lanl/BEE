# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

baseCommand: /clamr/CLAMR-master/clamr_cpuonly
# This is the stdout field which makes all stdout be captured in this file
# stderr is not currently implemented but it is also a thing
stdout: clamr_stdout.txt
# Arguments to the command
inputs:
  amr_type:
    # ? means the argument is optional
    # All of the ? here are legacy from the original CWL
    type: string?
    # Declare extra options
    # We support prefix and position
    inputBinding:
      # Prefix is the flag for cli command
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
  # Captures stdout. Name is arbitrary.
  clamr_stdout:
    # type is syntactic sugar to just grab the output file defined above
    # stdout:
    #     type: File
    #     outputBinding: 
    #       glob: clamr_stdout.txt
    #     stdout is easy shorthand
    type: stdout
  outdir:
    # directory is just another type. Scan the files for a directory with the name specified in glob
    # If you add a wildcard, it'd do expansion
    type: Directory
    outputBinding:
      # Glob can be either a constant string or have a wildcard 
      # TODO verify CWLs glob support
      glob: graphics_output/graph%05d.png
  time_log:
    type: File
    outputBinding:
      glob: total_execution_time.log
