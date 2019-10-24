class: CommandLineTool
cwlVersion: v1.0
baseCommand:
  - ch-run
inputs:
  cc_flags:
    default: '--no-home'
    type: string
    inputBinding:
      position: 1
  output_dir:
    type: string?
    inputBinding:
      position: 2
      prefix: '-b'
  scripts_dir:
    type: string?
    inputBinding:
      position: 3
      prefix: '-b'
  image:
    type: string
    inputBinding:
      position: 4
  command:
    default: sh
    type: string
    inputBinding:
      position: 6
  worker_script:
    type: string
    inputBinding:
      position: 7
  worker:
    type: string 
    inputBinding:
      position: 8
  split_done:
    type: string?
outputs:
  worker_done:
    type: string
    outputBinding:
      outputEval: $((inputs.output_dir + '/worker' + inputs.worker + '-done.txt'))
