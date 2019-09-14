class: CommandLineTool
cwlVersion: v1.0
baseCommand:
  - rm
inputs:
  image:
    type: string
    inputBinding:
      position: 2
  rm_flags:
    default: '-rf'
    type: string
    inputBinding:
      position: 1
  output_done:
    type: string?
  output_err_done:
    type: string?
outputs: []
