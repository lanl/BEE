# -*- mode: yaml; -*-

# cwltool scatter-dir.cwl scatter-dir-job.yml

class: Workflow
cwlVersion: v1.0

requirements:
  StepInputExpressionRequirement: {}
  ScatterFeatureRequirement: {}

inputs:
  deck_dir: Directory

outputs: []

steps:
  collect_decks:
    run:
      class: ExpressionTool
      requirements: { InlineJavascriptRequirement: {} }
      inputs:
        dir: Directory
      expression: '${return {"decks": inputs.dir.listing};}'
      outputs:
        decks: File[]
    in:
      dir: deck_dir
    out: [decks]
  crank:
    run:
      class: CommandLineTool
      inputs:
        deck:
          type: File
          inputBinding:
            position: 1
      outputs: []
      baseCommand: cat
    scatter: deck
    in:
      deck: collect_decks/decks
    out: []
