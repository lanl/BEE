# -*- mode: yaml; -*-

class: Workflow
cwlVersion: v1.0

requirements:
  InlineJavascriptRequirement: {}

inputs:
  outdir: string
  num: int
  pattern: string

outputs:
  dir:
    type: Directory
    outputSource: comp/dir
  movie:
    type: File
    outputSource: viz/movie

steps:
  comp:
    run:
      class: CommandLineTool
      inputs:
        outdir:
          type: string
          inputBinding: {position: 1}
        num:
          type: int
          inputBinding: {position: 2}
      outputs:
        dir:
          type: Directory
          outputBinding:
            glob: $(inputs.outdir)
      baseCommand: write-files.py
    in:
      outdir: outdir
      num: num
    out: [dir]
  viz:
    run:
      class: CommandLineTool
      inputs:
        indir:
          type: Directory
          inputBinding: {position: 1}
        pattern:
          type: string
          inputBinding: {position: 2}
      outputs:
        movie: 
          type: File
          outputBinding:
            glob: "*.mov"
      baseCommand: read-files.py
    in:
      indir: comp/dir
      pattern: pattern
    out: [movie]
