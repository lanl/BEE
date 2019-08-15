class: CommandLineTool
cwlVersion: v1.0
baseCommand:
  - echo 
inputs:
  - id: dir
    type: string
    inputBinding:
      position: 2
  - id: tarball
    type: string
    inputBinding:
      position: 1

outputs:
  - id: image
    type: string
    outputBinding:
      outputEval: 
        $((inputs.dir + '/' + ((inputs.tarball).split('/').slice(-1)[0]).slice(0,-7)))
