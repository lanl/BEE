class: Workflow
cwlVersion: v1.2

inputs:
  a: int
outputs: {}

steps:
  step0:
    run:
      class: CommandLineTool
      baseCommand: echo
      inputs:
        a:
          type: int
          inputBinding: {}
      outputs: []
    in:
      a: a
    out: []
