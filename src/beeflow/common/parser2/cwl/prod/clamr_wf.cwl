# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
##### CLAMR inputs #####
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
  clamr_stdout:
    type: File
    outputSource: clamr/clamr_stdout
  clamr_time_log:
    type: File
    outputSource: clamr/clamr_time_log
  clamr_movie:
    type: File
    outputSource: ffmpeg/ffmpeg_movie

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
    out: [clamr_stdout, clamr_outdir, clamr_time_log]
    hints:
        DockerRequirement:
            dockerImport: clamr_img.tar.gz
            dockerImageId: clamr

  ffmpeg:
    run: ffmpeg.cwl
    in:
      ffmpeg_input: clamr/clamr_outdir
      input_format: input_format
      frame_rate: frame_rate
      frame_size: frame_size
      pixel_format: pixel_format
      output_file: output_filename
    out: [ffmpeg_movie]
    requirements:
      InlineJavascriptRequirement: {}
 