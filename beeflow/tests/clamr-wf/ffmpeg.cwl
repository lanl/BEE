# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

baseCommand: ffmpeg
inputs:
  input_format:
    type: string?
    inputBinding:
      prefix: -f
      position: 1
  ffmpeg_input:
    type: string
    inputBinding:
      prefix: -i
      position: 2
  frame_rate:
    type: int?
    inputBinding:
      prefix: -r
      position: 3
  frame_size:
    type: string?
    inputBinding:
      prefix: -s
      position: 4
  pixel_format:
    type: string?
    inputBinding:
      prefix: -pix_fmt
      position: 5
  output_file:
    type: string
    inputBinding:
      position: 6

outputs:
  movie:
    type: File
    outputBinding:
      glob: $(inputs.output_file)
