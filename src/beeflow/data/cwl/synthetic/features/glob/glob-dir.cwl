# -*- mode: yaml; -*-

# PATH=$PATH:$PWD cwltool glob-dir.cwl --outdir outfiles --num 50
# rm -rf outfiles

class: Workflow
cwlVersion: v1.0

requirements:
  InlineJavascriptRequirement: {}

inputs:
  outdir: string
  num: int

outputs:
  dir:
    type: Directory
    outputSource: crank/dir

steps:
  crank:
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
      baseCommand: n-files-dir.py
    in:
      outdir: outdir
      num: num
    out: [dir]
