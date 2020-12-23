cwlVersion: v1.0
class: CommandLineTool

baseCommand: ffmpeg
stdout: ffmpeg-stdout.txt
stderr: ffmpeg-stdout.txt

requirements:
  - class: InitialWorkDirRequirement
    listing: $(inputs.inputdirectory.listing)

inputs:
  format:
    type: string?
    inputBinding:
      prefix: -f
      position: 0
  frame-rate:
    type: int?
    inputBinding:
      prefix: -r
      position: 1
  frame-size:
    type: string?
    inputBinding:
      prefix: -s
      position: 2
  pixel-format:
    type: string?
    inputBinding:
      prefix: -pix_fmt
      position: 3
  input-files-pattern:
    type: string
    inputBinding:
      prefix: -i
      position: 4
  outputfile:
    type: string
    inputBinding:
      position: -1
outputs:
  ffmpeg-output:
    type: File
    outputBinding:
      glob: $(inputs.outputfile)
  ffmpeg-stdout:
    type: stdout
