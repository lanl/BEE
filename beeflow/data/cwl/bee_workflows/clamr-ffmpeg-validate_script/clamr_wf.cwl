# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

# Main 3 components of workflow are inputs, outputs, and steps

inputs:
# All inputs go here for each step. No way to break them up.
# We should talk to the CWL people about that. 
##### CLAMR inputs #####
# takes ID:Type syntax
  grid_resolution: int
  max_levels: int
  time_steps: int
  steps_between_outputs: int
  steps_between_graphics: int
  graphics_type: string
##### FFMPEG inputs #####
  input_format: string
  frame_rate: int
  frame_size: string
  pixel_format: string
  output_filename: string

outputs:
# Outputs for all the steps
  clamr_stdout:
    type: File
    outputSource: clamr/clamr_stdout
  clamr_time_log:
    type: File
    outputSource: clamr/time_log
  clamr_movie:
    type: File
    outputSource: ffmpeg/movie
  ffmpeg_stderr:
    type: File
    outputSource: ffmpeg/ffmpeg_stderr

steps:
  clamr:
    run: clamr.cwl
    in:
      grid_res: grid_resolution
      max_levels: max_levels
      time_steps: time_steps
      output_steps: steps_between_outputs
      graphic_steps: steps_between_graphics
      graphics_type: graphics_type
    out: [clamr_stdout, outdir, time_log]
    hints:
        beeflow:ScriptRequirement:
            enabled: true
            pre_script: "pre_run.sh"
            post_script: "post_run.sh"
            shell: "/bin/bash"
        DockerRequirement:
            dockerFile: "Dockerfile.clamr-ffmpeg"
            beeflow:containerName: "clamr-ffmpeg"

  ffmpeg:
    run: ffmpeg.cwl
    in:
      input_format: input_format
      # input syntax is name: <step>/dependent_object
      ffmpeg_input: clamr/outdir
      frame_rate: frame_rate
      frame_size: frame_size
      pixel_format: pixel_format
      # Setting output file with file_name
      # output_filename set in wf inputs
      output_file: output_filename
    # Multiple outputs can be in array
    out: [movie, ffmpeg_stderr]
    hints:
        DockerRequirement:
            dockerFile: "Dockerfile.clamr-ffmpeg"
            beeflow:containerName: "clamr-ffmpeg"
