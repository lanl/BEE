# -*- mode: yaml; -*-

class: Workflow
cwlVersion: v1.0

requirements:
  StepInputExpressionRequirement: {}
  ScatterFeatureRequirement: {}
  InlineJavascriptRequirement: {}

inputs:
  outdir: string
  num: int
  modification: string

outputs:
  dir:
    type: Directory
    outputSource: comp/dir
  mods:
    type: Directory
    outputSource: mod/mods

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
  collect_viz_files:
    run:
      class: ExpressionTool
      inputs:
        dir: Directory
      expression: '${return {"viz_files": inputs.dir.listing};}'
      outputs:
        viz_files: File[]
    in:
      dir: viz/dir
    out: [files]
  mod:
    run:
      class: CommandLineTool
      inputs:
        viz_file:
          type: File
          inputBinding: {position: 1}
        modification:
          type: string
          inputBinding: {position: 2}
      outputs:
        movie: 
          type: File
          outputBinding:
            glob: "*.mov"
      baseCommand: mod-file.py
    scatter: viz_file
    in:
      viz_files: collect_viz_files/files
      modification: modification
    out: File[]
