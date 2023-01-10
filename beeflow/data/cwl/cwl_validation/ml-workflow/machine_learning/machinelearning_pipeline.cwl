#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow
inputs:
  experience: int
  interview: int
  test: int
  iterations: int
  datasetpath: string
outputs:
  expected_values:
    outputSource: predict/answer
    type: File
steps:
  read:
    run: /home/bee/cwl2/read_dataset_tool.cwl
    in:
      x: datasetpath
    out:
    - answer
  regress:
    run: /home/bee/cwl2/regress_tool.cwl
    in:
      x: iterations
    out:
    - answer
  decisiontree:
    run: /home/bee/cwl2/decision_tree_tool.cwl
    in:
      x: iterations
    out:
    - answer
  predict:
    run: /home/bee/cwl2/predict_tool.cwl
    in:
      x: experience
      y: interview
      z: test
    out:
    - answer
