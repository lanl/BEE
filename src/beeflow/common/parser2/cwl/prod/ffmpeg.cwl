# -*- mode: YAML; -*-

class: CommandLineTool
cwlVersion: v1.0

baseCommand: ffmpeg
inputs:
    ffmpeg_input:
        type: Directory
        inputBinding:
            prefix: -i
            valueFrom: ${ return self.path + "/graph%05d.png"; }
    input_format:
        type: string?
        inputBinding:
            prefix: -f
    frame_rate:
        type: int?
        inputBinding:
            prefix: -r
    frame_size:
        type: string?
        inputBinding:
            prefix: -s
    pixel_format:
        type: string?
        inputBinding:
            prefix: -pix_fmt
    output_file:
        type: string
        inputBinding:
            position: 7

outputs:
    ffmpeg_movie:
        type: File
        outputBinding:
            glob: $(inputs.output_file)
