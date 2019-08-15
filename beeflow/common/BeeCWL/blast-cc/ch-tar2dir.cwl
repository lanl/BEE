class: CommandLineTool
cwlVersion: v1.0
baseCommand:
  - ch-tar2dir
inputs:
  dir:
    type: string
    inputBinding:
      position: 2
  tarball:
    type: string
    inputBinding:
      position: 1

outputs:
  image:
    type: string
    outputBinding:
      outputEval: 
        $((inputs.dir + '/' + ((inputs.tarball).split('/').slice(-1)[0]).slice(0,-7)))
